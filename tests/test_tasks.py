from installlib.tasks import InstallOfflineWheel


def test_install_offline_wheel(mocker):
    mock_start_command = mocker.patch("installlib.tasks.start_command")
    mock_env = mocker.Mock(return_value=mocker.Mock(activate="activate"))

    path_to_wheel = r"C:\path\to\wheel.whl"

    task = InstallOfflineWheel(path_to_wheel, mock_env)

    task.execute()

    mock_start_command.assert_called_once_with(["activate", "&&", "python", "-m", "pip", "install", "--quiet", path_to_wheel])


def test_install_offline_wheel_extra_args(mocker):
    mock_start_command = mocker.patch("installlib.tasks.start_command")
    mock_env = mocker.Mock(return_value=mocker.Mock(activate="activate"))

    path_to_wheel = r"C:\path\to\wheel.whl"

    task = InstallOfflineWheel(path_to_wheel, mock_env, args=["--update", "--force-reinstall", "--no-deps"])

    task.execute()

    mock_start_command.assert_called_once_with(["activate", "&&", "python", "-m", "pip", "install", "--quiet", "--update", "--force-reinstall", "--no-deps", path_to_wheel])
