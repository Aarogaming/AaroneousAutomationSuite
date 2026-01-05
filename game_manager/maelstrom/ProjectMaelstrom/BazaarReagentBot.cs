using ProjectMaelstrom.Modules.ImageRecognition;
using ProjectMaelstrom.Utilities;
using System.Data;
using System.Threading;
using System.Timers;
using System.Windows.Forms;

namespace ProjectMaelstrom;

public partial class BazaarReagentBot : Form
{
    private System.Timers.Timer _runTimer;

    private bool _botStarted = false;

    private bool _isRunning = false;

    private readonly PlayerController _playerController = new PlayerController();

    public BazaarReagentBot()
    {
        InitializeComponent();
        TopLevel = false;
        FormBorderStyle = FormBorderStyle.None;
        ShowInTaskbar = false;
        TopMost = false;
        Dock = DockStyle.Fill;
        StartPosition = FormStartPosition.Manual;
        LoadPngFiles();
        _runTimer = new System.Timers.Timer(TimeSpan.FromMilliseconds(StateManager.BotTimerIntervalMs));
        _runTimer.Elapsed += BazaarLoop;
        _runTimer.AutoReset = true;
        this.FormClosing += BazaarReagentBot_FormClosing;

        // Apply system theme
        ThemeManager.ApplyTheme(this);
    }

    private void LoadPngFiles()
    {
        string directoryPath = $"{StorageUtils.GetAppPath()}/Bazaar/Reagents";

        if (Directory.Exists(directoryPath))
        {
            var fileNames = Directory.GetFiles(directoryPath, "*.png")
                                     .Select(Path.GetFileNameWithoutExtension)
                                     .ToList();

            listBox1.SelectionMode = SelectionMode.MultiSimple;
            listBox1.Items.Clear();
            listBox1.Items.AddRange(fileNames.Where(f => f != null).Cast<object>().ToArray());
        }
        else
        {
            MessageBox.Show("Directory not found: " + directoryPath, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private void startButton_Click(object sender, EventArgs e)
    {
        if (!_botStarted)
        {
            _runTimer.Start();
            _botStarted = true;
            btn.Text = "Stop Bot";
        }
        else
        {
            _runTimer?.Stop();
            _botStarted = false;
            btn.Text = "Start Bot";
        }
    }

    private void BazaarLoop(object? sender, ElapsedEventArgs e)
    {
        if (_isRunning)
        {
            return;
        }

        _isRunning = true;

        GeneralUtils.Instance.ResetCursorPosition();

        RefreshShop();

        if (listBox1.SelectedItems.Count > 0)
        {
            foreach (var item in listBox1.SelectedItems)
            {
                string? selectedName = item.ToString();

                if (selectedName == null)
                {
                    continue;
                }

                GetReagentLocation(selectedName);
            }
        }

        _isRunning = false;
    }

    private void GetReagentLocation(string itemName)
    {
        Point? item = ImageFinder.RetrieveTargetImagePositionInScreenshot($"{StorageUtils.GetAppPath()}/Bazaar/Reagents/{itemName}.png");

        if (item.HasValue)
        {
            label1.Text = "Found item";
            WinAPI.click(item.Value);
            BuyReagent();
        }
        else
        {
            label1.Text = "Not found";
        }
    }

    private void BuyReagent()
    {
        Point? buyMoreBtn = WaitForImage($"{StorageUtils.GetAppPath()}/Bazaar/buyMoreBtn.png", TimeSpan.FromSeconds(10));

        if (buyMoreBtn.HasValue)
        {
            WinAPI.click(buyMoreBtn.Value);

            Point? buyCount = WaitForImage($"{StorageUtils.GetAppPath()}/Bazaar/buyCount.png", TimeSpan.FromSeconds(10));

            if (buyCount.HasValue)
            {
                Point test = buyCount.Value;
                test.X += 10;
                WinAPI.click(test);
                _playerController.PressNumber9();
                _playerController.PressNumber9();
                _playerController.PressNumber9();
            }

            Point? buyBtn = WaitForImage($"{StorageUtils.GetAppPath()}/Bazaar/buyBtn.png", TimeSpan.FromSeconds(10));

            if (buyBtn.HasValue)
            {
                WinAPI.click(buyBtn.Value);
            }

            Point? okBtn = WaitForImage($"{StorageUtils.GetAppPath()}/Bazaar/okBtn.png", TimeSpan.FromSeconds(10));

            if (okBtn.HasValue)
            {
                WinAPI.click(okBtn.Value);
            }
        }
    }

    private void RefreshShop()
    {
        Point? refreshBtn = WaitForImage($"{StorageUtils.GetAppPath()}/Bazaar/refreshBtn.png", TimeSpan.FromSeconds(10));

        if (refreshBtn.HasValue)
        {
            WinAPI.click(refreshBtn.Value);
        }
    }

    private Point? WaitForImage(string imagePath, TimeSpan timeout, int pollDelayMs = 200)
    {
        DateTime start = DateTime.UtcNow;
        Point? location = ImageFinder.RetrieveTargetImagePositionInScreenshot(imagePath);

        while (location == null && DateTime.UtcNow - start < timeout)
        {
            Thread.Sleep(pollDelayMs);
            location = ImageFinder.RetrieveTargetImagePositionInScreenshot(imagePath);
        }

        return location;
    }

    private void BazaarReagentBot_FormClosing(object? sender, FormClosingEventArgs e)
    {
        _runTimer?.Stop();
        _runTimer?.Dispose();
    }
}
