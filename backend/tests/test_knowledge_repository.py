import numpy as np
import pytest

from app.repositories.knowledge import KnowledgeRepository, Passage


def _repo() -> KnowledgeRepository:
    passages = [
        Passage(id="tarifs", title="Tarifs", text="Le tarif d'une promenade est de 15 euros."),
        Passage(id="secteur", title="Secteur", text="J'interviens à Paris et dans les environs."),
        Passage(id="animaux", title="Animaux", text="Je m'occupe des chiens et des chats."),
    ]
    vectors = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )
    return KnowledgeRepository(passages, vectors)


def test_search_returns_best_match_first():
    repo = _repo()
    results = repo.search(np.array([0.9, 0.1, 0.0], dtype=np.float32), k=3)

    assert results[0].passage.id == "tarifs"
    assert results[0].score == pytest.approx(0.9938837, abs=1e-6)


def test_search_respects_k():
    repo = _repo()
    results = repo.search(np.array([1.0, 0.0, 0.0], dtype=np.float32), k=2)

    assert len(results) == 2


def test_search_on_empty_repository_returns_no_results():
    repo = KnowledgeRepository([], np.empty((0, 0), dtype=np.float32))

    assert repo.is_empty is True
    assert repo.search(np.array([1.0, 0.0], dtype=np.float32), k=4) == []


def test_search_with_zero_query_vector_returns_no_results():
    repo = _repo()

    assert repo.search(np.array([0.0, 0.0, 0.0], dtype=np.float32), k=3) == []


def test_load_missing_index_file_returns_empty_repository(tmp_path):
    repo = KnowledgeRepository.load(tmp_path / "missing.npz", expected_model="mistral-embed")

    assert repo.is_empty is True


def test_load_rejects_index_built_with_a_different_model(tmp_path):
    index_path = tmp_path / "index.npz"
    np.savez(
        index_path,
        ids=np.array(["a"]),
        titles=np.array(["A"]),
        texts=np.array(["texte"]),
        vectors=np.array([[1.0, 0.0]], dtype=np.float32),
        model=np.array("old-model"),
    )

    repo = KnowledgeRepository.load(index_path, expected_model="mistral-embed")

    assert repo.is_empty is True


def test_load_reads_a_valid_index(tmp_path):
    index_path = tmp_path / "index.npz"
    np.savez(
        index_path,
        ids=np.array(["a", "b"]),
        titles=np.array(["A", "B"]),
        texts=np.array(["texte a", "texte b"]),
        vectors=np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32),
        model=np.array("mistral-embed"),
    )

    repo = KnowledgeRepository.load(index_path, expected_model="mistral-embed")

    assert repo.is_empty is False
    results = repo.search(np.array([1.0, 0.0], dtype=np.float32), k=1)
    assert results[0].passage.id == "a"
