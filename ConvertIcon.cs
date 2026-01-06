using System.Drawing;
using System.IO;

class ConvertIcon
{
    static void Main(string[] args)
    {
        if (args.Length < 2)
        {
            System.Console.WriteLine("Usage: ConvertIcon <input.jpg> <output.ico>");
            return;
        }
        var input = args[0];
        var output = args[1];
        using var img = Image.FromFile(input);
        using var bmp = new Bitmap(img, new Size(256, 256));
        using var iconStream = new FileStream(output, FileMode.Create);
        Icon.FromHandle(bmp.GetHicon()).Save(iconStream);
    }
}
