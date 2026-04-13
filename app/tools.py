def mock_lead_capture(name: str, email: str, platform: str) -> str:
    """
    Mock tool to capture lead information.
    Executed only after name, email, and platform are successfully collected.
    """
    print(f"Lead captured successfully: {name}, {email}, {platform}")
    return f"Lead captured successfully for {name}!"
