# Code Citations

## License: GPL-3.0
https://github.com/CoderJoeW/AutoWizard101/blob/f2721fa5883f6c733977de6746ce1b0d86c15974/ProjectMaelstrom/ProjectMaelstrom/Main.cs

```
await ImageHelpers.ExtractTextFromImage(imagePath);

        string[] extractedTextArray = extractedText.Split(new[] { Environment.NewLine }, StringSplitOptions.None);

        string mana = "";

        for (int i = 0; i < extractedTextArray.Length; i++)
        {
            if (extractedTextArray[i] == "GOLD")
            {
                mana = extractedTextArray[i - 1];
            }
        }

        string[] manaArray = mana.Split(new[] { "/" }, StringSplitOptions.None);

        StateManager.Instance.CurrentMana = int.Parse(manaArray[0]);
        StateManager.Instance.MaxMana = int.
```

