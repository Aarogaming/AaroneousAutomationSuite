using ProjectMaelstrom.Modules.ImageRecognition;

namespace ProjectMaelstrom.Utilities;

internal class CombatUtils : Util
{
    public bool IsInBattle()
    {
        Point? spellbook = ImageFinder.RetrieveTargetImagePositionInScreenshot($"{StorageUtils.GetAppPath()}/Combat/Utils/spellbook.png");

        if (spellbook.HasValue)
        {
            return false;
        }

        return true;
    }

    public bool UseCard(string cardName)
    {
        string[] images = Directory.GetFiles($"{StorageUtils.GetAppPath()}/Combat/Cards/{cardName}/");
        var start = DateTime.UtcNow;
        var timeout = TimeSpan.FromSeconds(10);

        foreach (var image in images)
        {
            Point? card = ImageFinder.RetrieveTargetImagePositionInScreenshot(image);

            if (card.HasValue)
            {
                _playerController.Click(card.Value);
                return true;
            }

            if (DateTime.UtcNow - start > timeout)
            {
                Logger.Log($"[UseCard] Timeout searching for card '{cardName}'.");
                return false;
            }

            Thread.Sleep(150);
        }

        Logger.Log($"[UseCard] No images found for card '{cardName}'.");
        return false;
    }

    public bool IsMyTurn()
    {
        Point? passBtn = ImageFinder.RetrieveTargetImagePositionInScreenshot($"{StorageUtils.GetAppPath()}/Combat/Utils/passbutton.png");

        if (passBtn.HasValue)
        {
            return true;
        }

        return false;
    }

    public void Pass()
    {
        Point? passBtn = ImageFinder.RetrieveTargetImagePositionInScreenshot($"{StorageUtils.GetAppPath()}/Combat/Utils/passbutton.png");

        if (passBtn.HasValue)
        {
            WinAPI.click(passBtn.Value);
        }
    }

    public bool IsOutsideDungeon()
    {
        Point? sigil = ImageFinder.RetrieveTargetImagePositionInScreenshot($"{StorageUtils.GetAppPath()}/Combat/Utils/sigil.png");

        if (sigil.HasValue)
        {
            return true;
        }

        return false;
    }
}
