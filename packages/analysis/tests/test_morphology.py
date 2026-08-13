from secondear_analysis.morphology import ConservativeEnglishMorphology


def test_conservative_morphology_requires_one_dictionary_backed_candidate() -> None:
    morphology = ConservativeEnglishMorphology({"run", "running", "try", "tried", "unknown"})

    assert morphology.lemma("running") == "run"
    assert morphology.lemma("tried") == "try"
    assert morphology.lemma("unknown") == "unknown"
    assert morphology.lemma("inventedness") is None


def test_ambiguous_morphology_is_not_used() -> None:
    morphology = ConservativeEnglishMorphology({"rate", "rated", "rat"})

    assert morphology.lemma("rated") is None
