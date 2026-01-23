from unittest.mock import patch
from src.utils.audit import publish_audit


@patch("src.utils.audit.send_message")
def test_publish_audit_sends_message(mock_send):
    publish_audit(
        feature="test",
        action="CREATE",
        actor="ADMIN",
        old=None,
        new={"enabled": True},
    )

    mock_send.assert_called_once()

    payload = mock_send.call_args[0][0]
    assert '"feature": "test"' in payload
    assert '"action": "CREATE"' in payload
