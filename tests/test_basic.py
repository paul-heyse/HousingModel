from HousingModel import ping


def test_ping():
    assert ping() == "pong"
