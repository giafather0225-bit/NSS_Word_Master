"""수동 단어 입력 API 테스트 — POST/PATCH/DELETE /api/lessons/{id}/words."""
import pytest
from tests.conftest import MOCK_VOCAB_JSON


class TestCreateManualWord:

    def test_create_word_returns_201(self, client, sample_lesson):
        res = client.post(
            f"/api/words/lesson/{sample_lesson.id}",
            json={
                "word": "abundant",
                "definition": "existing in large quantities",
                "example": "The forest has abundant wildlife.",
                "pos": "adj.",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["word"] == "abundant"
        assert data["source_type"] == "manual"
        assert data["definition"] == "existing in large quantities"

    def test_source_type_is_manual(self, client, sample_lesson):
        res = client.post(
            f"/api/words/lesson/{sample_lesson.id}",
            json={"word": "resilient", "definition": "able to recover quickly"},
        )
        assert res.status_code == 201
        assert res.json()["source_type"] == "manual"

    def test_study_item_id_is_linked(self, client, sample_lesson):
        """words 저장 시 study_items 도 생성되어 study_item_id 가 연결돼야 함."""
        res = client.post(
            f"/api/words/lesson/{sample_lesson.id}",
            json={"word": "swift", "definition": "moving with great speed",
                  "example": "The swift bird flew away.", "pos": "adj."},
        )
        assert res.status_code == 201
        assert res.json()["study_item_id"] is not None

    def test_duplicate_word_returns_409(self, client, sample_lesson):
        payload = {"word": "unique_word_xyz", "definition": "one of a kind"}
        client.post(f"/api/words/lesson/{sample_lesson.id}", json=payload)
        res = client.post(f"/api/words/lesson/{sample_lesson.id}", json=payload)
        assert res.status_code == 409

    def test_missing_word_field_returns_422(self, client, sample_lesson):
        res = client.post(
            f"/api/words/lesson/{sample_lesson.id}",
            json={"definition": "no word provided"},
        )
        assert res.status_code == 422

    def test_missing_definition_returns_422(self, client, sample_lesson):
        res = client.post(
            f"/api/words/lesson/{sample_lesson.id}",
            json={"word": "test"},
        )
        # definition 은 필수이므로 422
        assert res.status_code == 422

    def test_nonexistent_lesson_returns_404(self, client):
        res = client.post(
            "/api/words/lesson/99999",
            json={"word": "test", "definition": "a test word"},
        )
        assert res.status_code == 404

    def test_example_is_optional(self, client, sample_lesson):
        res = client.post(
            f"/api/words/lesson/{sample_lesson.id}",
            json={"word": "optional_ex_test", "definition": "no example provided"},
        )
        assert res.status_code == 201
        assert res.json()["example"] == ""

    def test_pos_is_optional(self, client, sample_lesson):
        res = client.post(
            f"/api/words/lesson/{sample_lesson.id}",
            json={"word": "pos_optional_test", "definition": "part of speech optional"},
        )
        assert res.status_code == 201
        assert res.json()["pos"] == ""


class TestUpdateManualWord:

    def _create(self, client, lesson_id, word="update_target"):
        res = client.post(
            f"/api/words/lesson/{lesson_id}",
            json={"word": word, "definition": "original definition", "pos": "n."},
        )
        assert res.status_code == 201
        return res.json()

    def test_patch_definition(self, client, sample_lesson):
        word = self._create(client, sample_lesson.id, "patchtarget1")
        res = client.patch(
            f"/api/words/lesson/{sample_lesson.id}/{word['id']}",
            json={"definition": "updated definition"},
        )
        assert res.status_code == 200
        assert res.json()["definition"] == "updated definition"

    def test_patch_example(self, client, sample_lesson):
        word = self._create(client, sample_lesson.id, "patchtarget2")
        res = client.patch(
            f"/api/words/lesson/{sample_lesson.id}/{word['id']}",
            json={"example": "A new example sentence."},
        )
        assert res.status_code == 200
        assert res.json()["example"] == "A new example sentence."

    def test_patch_nonexistent_word_returns_404(self, client, sample_lesson):
        res = client.patch(
            f"/api/words/lesson/{sample_lesson.id}/99999",
            json={"definition": "updated"},
        )
        assert res.status_code == 404


class TestDeleteManualWord:

    def _create(self, client, lesson_id, word="delete_target"):
        res = client.post(
            f"/api/words/lesson/{lesson_id}",
            json={"word": word, "definition": "to be deleted"},
        )
        assert res.status_code == 201
        return res.json()

    def test_delete_returns_204(self, client, sample_lesson):
        word = self._create(client, sample_lesson.id, "deltarget1")
        res = client.delete(
            f"/api/words/lesson/{sample_lesson.id}/{word['id']}"
        )
        assert res.status_code == 204

    def test_deleted_word_not_in_list(self, client, sample_lesson):
        word = self._create(client, sample_lesson.id, "deltarget2")
        client.delete(f"/api/words/lesson/{sample_lesson.id}/{word['id']}")

        list_res = client.get(f"/api/storage/lessons/{sample_lesson.id}/words")
        ids = [w["id"] for w in list_res.json().get("words", [])]
        assert word["id"] not in ids

    def test_delete_nonexistent_returns_404(self, client, sample_lesson):
        res = client.delete(f"/api/words/lesson/{sample_lesson.id}/99999")
        assert res.status_code == 404
