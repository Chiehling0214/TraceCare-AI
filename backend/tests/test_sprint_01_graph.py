def _patient_id(client, code: str) -> int:
    payload = client.get("/api/patients").json()
    return next(item["id"] for item in payload["items"] if item["patient_code"] == code)


def test_patient_graph_contains_expected_nodes_edges_and_directions(seeded_client):
    seeded_client.post("/api/prototype/run-analysis")
    contradiction = seeded_client.post("/api/prototype/run-contradiction-analysis").json()
    p001 = next(item for item in contradiction["results"] if item["patient_code"] == "P001")
    patient_id = p001["patient_id"]

    response = seeded_client.get(f"/api/patients/{patient_id}/evidence-graph")
    assert response.status_code == 200
    graph = response.json()
    node_types = {node["type"] for node in graph["nodes"]}
    assert {"patient", "lab", "document", "fact", "event"} <= node_types

    edges = {(edge["source"].split(":")[0], edge["target"].split(":")[0], edge["relation"]) for edge in graph["edges"]}
    assert ("patient", "document", "HAS_DOCUMENT") in edges
    assert ("document", "fact", "CONTAINS_FACT") in edges
    assert ("fact", "event", "ASSERTED_FACT") in edges
    assert ("fact", "event", "DENIED_FACT") in edges
    assert ("lab", "event", "PREVIOUS_VALUE") in edges
    assert ("lab", "event", "CURRENT_VALUE") in edges

    assert len({edge["id"] for edge in graph["edges"]}) == len(graph["edges"])
    assert all("p002" not in node.get("metadata", {}).get("source_document", "").lower() for node in graph["nodes"])


def test_event_graph_is_scoped_to_one_event(seeded_client):
    seeded_client.post("/api/prototype/run-analysis")
    contradiction = seeded_client.post("/api/prototype/run-contradiction-analysis").json()
    contradiction_event_id = next(
        item["event_id"] for item in contradiction["results"] if item["patient_code"] == "P001"
    )

    response = seeded_client.get(f"/api/events/{contradiction_event_id}/evidence-graph")
    assert response.status_code == 200
    graph = response.json()
    event_nodes = [node for node in graph["nodes"] if node["type"] == "event"]
    assert len(event_nodes) == 1
    assert event_nodes[0]["metadata"]["rule_id"] == "ALLERGY_CONTRADICTION"
    assert any(edge["relation"] == "SOURCE_DOCUMENT" for edge in graph["edges"])
    assert all(edge["target"] == f"event:{contradiction_event_id}" or edge["relation"].startswith("HAS") or edge["relation"] == "CONTAINS_FACT" for edge in graph["edges"])


def test_graph_apis_return_404_for_unknown_resources(seeded_client):
    assert seeded_client.get("/api/patients/999/evidence-graph").status_code == 404
    assert seeded_client.get("/api/events/999/evidence-graph").status_code == 404


def test_graph_does_not_link_different_patients(seeded_client):
    seeded_client.post("/api/prototype/run-contradiction-analysis")
    p002_id = _patient_id(seeded_client, "P002")

    graph = seeded_client.get(f"/api/patients/{p002_id}/evidence-graph").json()
    assert all(node["id"] != f"patient:{_patient_id(seeded_client, 'P001')}" for node in graph["nodes"])
    assert not any(
        node["type"] == "event" and node["metadata"]["rule_id"] == "ALLERGY_CONTRADICTION"
        for node in graph["nodes"]
    )
