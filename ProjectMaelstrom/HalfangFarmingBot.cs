using ProjectMaelstrom.Modules.ImageRecognition;
using ProjectMaelstrom.Utilities;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows.Forms;

namespace ProjectMaelstrom;

public partial class HalfangFarmingBot : Form
{
    [DllImport("user32.dll", SetLastError = true)]
    public static extern short GetAsyncKeyState(int vKey);

    [DllImport("user32.dll")]
    private static extern IntPtr GetMessageExtraInfo();

    private readonly System.Windows.Forms.Timer _runTimer;

    private readonly PlayerController _playerController = new PlayerController();
    private readonly CombatUtils _combatUtils = new CombatUtils();

    private bool _joiningDungeon = false;
    private bool _inDungeon = false;
    private bool _battleStarted = false;
    private bool _battleWon = false;
    private bool _botStarted = false;

    private bool _isRunning = false;

    public HalfangFarmingBot()
    {
        InitializeComponent();
        TopLevel = false;
        FormBorderStyle = FormBorderStyle.None;
        ShowInTaskbar = false;
        TopMost = false;
        Dock = DockStyle.Fill;
        StartPosition = FormStartPosition.Manual;
        _runTimer = new System.Windows.Forms.Timer
        {
            Interval = StateManager.BotTimerIntervalMs
        };
        _runTimer.Tick += DungeonLoop;
        this.FormClosing += HalfangFarmingBot_FormClosing;

        // Apply system theme
        ThemeManager.ApplyTheme(this);

        SetPendingStates("Waiting to start");
    }

    private void HalfangFarmingBot_Load(object sender, EventArgs e) { }

    private void DungeonLoop(object? sender, EventArgs e)
    {
        if (_isRunning)
        {
            return;
        }

        _isRunning = true;

        if (!GeneralUtils.Instance.IsGameVisible())
        {
            SetPendingStates("Wizard101 not detected");
            _isRunning = false;
            return;
        }

        if (_combatUtils.IsOutsideDungeon() && !_joiningDungeon && !_inDungeon)
        {
            UpdateBotState("Outside dungeon joining");
            HandleJoinDungeon();
        }
        else if (_inDungeon && !_battleStarted && !_battleWon)
        {
            UpdateBotState("Battle not started joining");
            _playerController.MoveForward();

            var waitStart = DateTime.UtcNow;
            while (!_battleStarted && DateTime.UtcNow - waitStart < TimeSpan.FromSeconds(15))
            {
                if (_combatUtils.IsInBattle())
                {
                    _battleStarted = true;
                    break;
                }
                Thread.Sleep(100);
            }

            if (!_battleStarted)
            {
                UpdateBotState("Battle start timeout");
            }
        }
        else if (_battleStarted && !_battleWon)
        {
            if (_combatUtils.IsMyTurn())
            {
                HandleMyTurn();
            }
            else
            {
                UpdateBotState("Waiting for turn");
            }

            Point? spellbook = ImageFinder.RetrieveTargetImagePositionInScreenshot($"{StorageUtils.GetAppPath()}/General/spellbook.png");

            if (spellbook != null)
            {
                HandleBattleOver();
            }
        }
        else if (_battleWon)
        {
            HandleBattleWon();
        }

        _isRunning = false;
    }

    private void HandleJoinDungeon()
    {
        UpdateJoiningDungeonState(true);
        UpdateBotState("Outside dungeon joining");
        GeneralUtils.Instance.ResetCursorPosition();
        _playerController.Interact();

        DateTime start = DateTime.UtcNow;
        Point? loadingIcon = ImageFinder.RetrieveTargetImagePositionInScreenshot($"{StorageUtils.GetAppPath()}/Halfang/loading.png");

        while (loadingIcon == null && DateTime.UtcNow - start < TimeSpan.FromSeconds(15))
        {
            Thread.Sleep(250);
            loadingIcon = ImageFinder.RetrieveTargetImagePositionInScreenshot($"{StorageUtils.GetAppPath()}/Halfang/loading.png");
        }

        if (loadingIcon.HasValue)
        {
            UpdateJoiningDungeonState(false);
            UpdateInDungeonState(true);
        }
        else
        {
            UpdateBotState("Failed to join dungeon (timeout)");
            UpdateJoiningDungeonState(false);
        }
    }

    private void HandleMyTurn()
    {
        UpdateBattleState(true);
        UpdateBotState("My turn");
        bool result = _combatUtils.UseCard("meteor");

        if (!result)
        {
            _combatUtils.Pass();
        }

        GeneralUtils.Instance.ResetCursorPosition();
    }

    private void HandleBattleOver()
    {
        if (_battleStarted)
        {
            UpdateBotState("Battle won");
            UpdateBattleState(false);
            UpdateBattleWonState(true);
        }
    }

    private void HandleBattleWon()
    {
        bool teleported = GeneralUtils.Instance.Teleport();

        if (teleported)
        {
            GeneralUtils.Instance.ResetCursorPosition();
            UpdateBattleWonState(false);
            UpdateInDungeonState(false);
        }
    }

    private void button1_Click(object sender, EventArgs e)
    {
        if (!_botStarted)
        {
            _runTimer.Start();
            _botStarted = true;
            button1.Text = "Stop Bot";
        }
        else
        {
            _runTimer?.Stop();
            _botStarted = false;
            button1.Text = "Start Bot";
            SetPendingStates("Bot stopped");
        }
    }

    private void UpdateBattleState(bool state)
    {
        _battleStarted = state;
        inBattleText.Text = state ? "Yes" : "No";
        inBattleText.ForeColor = state ? Color.Green : Color.Red;
    }

    private void UpdateBattleWonState(bool state)
    {
        _battleWon = state;
        battleWonText.Text = state ? "Yes" : "No";
        battleWonText.ForeColor = state ? Color.Green : Color.Red;
    }

    private void UpdateJoiningDungeonState(bool state)
    {
        _joiningDungeon = state;
        joiningDungeonText.Text = state ? "Yes" : "No";
        joiningDungeonText.ForeColor = state ? Color.Green : Color.Red;
    }

    private void UpdateInDungeonState(bool state)
    {
        _inDungeon = state;
        inDungeonText.Text = state ? "Yes" : "No";
        inDungeonText.ForeColor = state ? Color.Green : Color.Red;
    }

    private void UpdateBotState(string state)
    {
        botState.Text = state;
    }

    private void HalfangFarmingBot_FormClosing(object? sender, FormClosingEventArgs e)
    {
        _runTimer?.Stop();
        _runTimer?.Dispose();
    }

    private void SetPendingStates(string? message = null)
    {
        const string pendingText = "Pending";
        Color pendingColor = Color.DarkOrange;

        inBattleText.Text = pendingText;
        inBattleText.ForeColor = pendingColor;
        battleWonText.Text = pendingText;
        battleWonText.ForeColor = pendingColor;
        joiningDungeonText.Text = pendingText;
        joiningDungeonText.ForeColor = pendingColor;
        inDungeonText.Text = pendingText;
        inDungeonText.ForeColor = pendingColor;

        if (!string.IsNullOrWhiteSpace(message))
        {
            UpdateBotState(message);
        }
    }
}
