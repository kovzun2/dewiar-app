"""Эксперт Радара учится по материалам и использует общую память в Студии и чате."""
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))


class Settings:
    def __init__(self):
        self.data = {"insight": {"mission": "Инди-продукты, микро-SaaS и автоматизация"}, "ui": {"lang": "ru"}}

    def get(self, key):
        return self.data.get(key)

    def update(self, patch):
        for key, values in patch.items():
            self.data.setdefault(key, {}).update(values)


def run(root):
    os.environ["DEWIAR_STATE_DIR"] = str(root / "state")
    os.environ["DEWIAR_CONFIG_DIR"] = str(root / "config")
    import engine_insight as engine
    from tools_docs import t_insight_ask

    eng = SimpleNamespace(s=Settings(), emit=lambda *a, **kw: None)
    radar = eng.insight = engine.Radar(eng, root / "radar")
    radar.st.add_sources("https://example.org/feed.xml")
    src = radar.st.sources()[0]
    url = "https://example.org/billing-case"
    quote = "BillingFox достиг $1 200 MRR через 6 месяцев."
    radar.st.add_items(src, [{"title": "BillingFox", "url": url, "ts": int(time.time()) - 35 * 86400,
                              "text": "Короткое описание продукта из ленты."}])
    item = radar.st.items()[0]
    # Старый разбор существует до обновления приложения. Цифра находится только в самой статье.
    radar.st.set_analysis(item["id"], {"summary": "Запуск продукта", "why": "", "type": "news",
                                      "signal": 5, "tags": [], "entities": []})
    radar.fetch_study = lambda link: f"<article>{'Предыстория проекта. ' * 105}<p>{quote}</p></article>"
    question = "Какой микро-SaaS запустить и как его монетизировать?"

    def study(system, user, max_tokens=700):
        assert quote in user, "эксперт должен прочитать статью за пределами выдержки ленты"
        return json.dumps({"summary": "Разбор BillingFox", "signal": 5, "findings": [
            {"subject": "BillingFox", "kind": "revenue", "quote": quote},
            {"subject": "BillingFox", "kind": "pricing", "quote": "Подписка стоила $200 в месяц."},
        ]})

    radar._ask = study
    assert radar.analyze(2, paced=False) == 1, "имеющийся материал должен попасть на изучение в рамках лимита"
    view = engine.command(eng, "insight_mind", {})["expert"]
    assert view["studied"] == 1 and view["cases"] == 1
    assert [f["quote"] for f in view["recent"][0]["findings"]] == [quote], "вымышленную цитату следует отбросить"
    assert radar.analyze(2, paced=False) == 0, "повторный такт не расходует бюджет на изученный кейс"
    print("✅ Изучение старых статей в пределах лимита, проверка цитат и прогресс")

    engine.command(eng, "insight_mark", {"id": item["id"], "fb": -1})
    assert not engine.command(eng, "insight_mind", {})["expert"]["recent"]
    assert not engine.question(eng, question, expert=True)["refs"]
    # После перезапуска и удаления материала из ленты ссылка должна открывать оригинал.
    radar.st.save("items", [])
    radar = eng.insight = engine.Radar(eng, root / "radar")
    assert not engine.question(eng, question, expert=True)["refs"], "оценка сохраняется отдельно от ленты"
    engine.command(eng, "insight_mark", {"id": item["id"], "fb": 0})

    def answer(system, user, max_tokens=700):
        assert "модель оплаты" in system and "готовность платить" in system
        assert quote in user and question in user, "вопрос о продукте должен использовать архив кейсов"
        assert "Разбор BillingFox" not in user, "резюме модели не является цитатой из источника"
        return "Автоматизируйте сверку платежей.\n• Старт — предложите платный пилот [1]."

    radar._ask = answer
    studio = engine.command(eng, "insight_question", {"q": question, "expert": True})
    chat = json.loads(t_insight_ask({"query": question, "expert": True}, {"engine": eng}))
    assert studio == chat and studio["expert"]
    assert studio["refs"][0]["url"] == url and not studio["refs"][0]["id"]
    assert "платный пилот" in studio["text"]
    assert "items" in json.loads(t_insight_ask({"query": "BillingFox"}, {"engine": eng}))
    print("✅ Одна память в Студии и чате, источник доступен после перезапуска и очистки ленты")

    assert engine.command(eng, "insight_expert_name", {"name": "Мира"})["name"] == "Мира"
    assert radar.expert_query("Мира, какой продукт запустить?") == "какой продукт запустить?"
    assert radar.expert_query("мира предложи продукт") == "предложи продукт"
    assert not radar.expert_query("Это история о том, что Мира писала про SaaS")
    for lang in ("ru", "en"):
        labels = json.loads((ROOT / "data" / "i18n" / f"{lang}.json").read_text(encoding="utf-8"))
        assert radar.expert_query(labels["insight.expert.ask_prefix"] + " " + question) == question
    from modules import wanted
    assert "radar" in wanted("Ask the Radar expert for an idea")
    print("✅ Эксперта можно позвать по имени или через Радар")

    def long_answer(system, user, max_tokens=700):
        assert "Старая ссылка" in user and "[2]" not in user
        return "Главное.\n• Первый кейс [01]\n• " + "деталь " * 500 + "Конец рекомендации."

    radar._ask = long_answer
    longer = engine.question(eng, "Почему?", expert=True, history=[{"q": question, "a": "Старая ссылка [2]."}])
    assert len(longer["text"]) > 3000 and longer["text"].endswith("Конец рекомендации.")
    assert "Первый кейс [1]" in longer["text"] and [ref["n"] for ref in longer["refs"]] == [1]
    import insight
    sample = {"items": [{"id": "past-limit", "title": "За пределами ответа"}]}
    assert not insight.parse_answer("Текст " * 600 + "[1]", sample)["refs"]
    print("✅ Длинный ответ сохраняется и использует ссылки только из текущей подборки")

    engine.command(eng, "insight_mission", {"text": "Фотография"})
    assert engine.command(eng, "insight_mind", {})["expert"]["studied"] == 0
    radar.st.save("brief", {"headline": "Старый бриф по микро-SaaS"})
    radar._ask = lambda *_a, **_kw: (_ for _ in ()).throw(AssertionError("новой миссии нужны свои кейсы"))
    empty = engine.command(eng, "insight_question", {"q": "Что предложишь?", "expert": True})
    assert empty["expert"] == "Мира" and not empty["refs"]
    print("✅ Миссия ограничивает круг накопленных знаний")

    undated = "https://example.org/photo-case"
    radar.st.add_items(src, [{"title": "Студия съёмки", "url": undated, "text": "Анонс из ленты"}])

    def temporarily_unavailable(_url):
        raise TimeoutError("Страница временно недоступна")

    radar.fetch_study = temporarily_unavailable
    radar._ask = lambda *_a, **_kw: json.dumps({"summary": "Анонс", "findings": []})
    assert radar.analyze(2, paced=False) == 1 and radar.analyze(2, paced=False) == 0
    now = time.time()
    revenue = "Студия заработала 650 евро за первый месяц."
    radar.fetch_study = lambda _url: f"<article><p>{revenue}</p></article>"
    radar._ask = lambda *_a, **_kw: json.dumps({"summary": "Итоги", "findings": [
        {"subject": "Студия съёмки", "kind": "revenue", "quote": revenue},
    ]})
    with patch("engine_insight.time.time", return_value=now + 86400):
        assert radar.analyze(2, paced=False) == 1, "временный сбой должен оставлять возможность перечитать статью"
        assert radar.analyze(2, paced=False) == 0
    recent = engine.command(eng, "insight_mind", {})["expert"]["recent"][0]
    assert recent["url"] == undated and recent["ts"] == 0 and recent["at"] > now
    assert recent["findings"][0]["quote"] == revenue
    print("✅ После сбоя эксперт возвращается к статье и хранит дату изучения отдельно от даты публикации")

    radar.st.add_items(src, [{"title": "Старый кейс", "url": "https://example.org/older"}])
    older = radar.st.items()[-1]
    radar.st.set_analysis(older["id"], {"summary": "Старый разбор", "signal": 4})
    radar._ask = lambda *_a, **_kw: "ответ без JSON"
    start = time.time()
    for day in range(3):
        with patch("engine_insight.time.time", return_value=start + day * 2 * 86400):
            assert radar.analyze(2, paced=False) == 1
            assert radar.analyze(2, paced=False) == 0, "ошибка разбора не должна повторяться на следующем такте"
    with patch("engine_insight.time.time", return_value=start + 7 * 86400):
        assert radar.analyze(2, paced=False) == 0, "число повторов ограничено"
    assert radar.st.items()[-1]["a"]["summary"] == "Старый разбор"
    assert engine.command(eng, "insight_mind", {})["expert"]["studied"] == 1
    print("✅ Невалидный разбор старой статьи повторяется с задержкой и ограниченным числом попыток")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as directory:
        run(Path(directory))
