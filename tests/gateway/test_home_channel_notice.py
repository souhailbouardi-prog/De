from gateway.run import GatewayRunner


def test_home_channel_notice_reads_like_setup_copy():
    notice = GatewayRunner._build_home_channel_notice("telegram")

    assert notice.startswith("⚙️ Setup notice:")
    assert "Telegram home channel is not set yet." in notice
    assert "/sethome" in notice
    assert "cron job results" in notice
    assert "cross-platform messages" in notice
    assert "No home channel is set" not in notice
