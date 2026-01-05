namespace ProjectMaelstrom
{
    partial class MacroRecorderForm
    {
        /// <summary>
        ///  Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        ///  Clean up any resources being used.
        /// </summary>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        private void InitializeComponent()
        {
            startStopButton = new Button();
            saveButton = new Button();
            macroNameText = new TextBox();
            label1 = new Label();
            statusLabel = new Label();
            commandsList = new ListBox();
            SuspendLayout();
            // 
            // startStopButton
            // 
            startStopButton.Location = new Point(14, 14);
            startStopButton.Name = "startStopButton";
            startStopButton.Size = new Size(180, 38);
            startStopButton.TabIndex = 0;
            startStopButton.Text = "Start Recording";
            startStopButton.UseVisualStyleBackColor = true;
            startStopButton.Click += startStopButton_Click;
            // 
            // saveButton
            // 
            saveButton.Location = new Point(14, 124);
            saveButton.Name = "saveButton";
            saveButton.Size = new Size(180, 38);
            saveButton.TabIndex = 1;
            saveButton.Text = "Save Macro";
            saveButton.UseVisualStyleBackColor = true;
            saveButton.Click += saveButton_Click;
            // 
            // macroNameText
            // 
            macroNameText.Location = new Point(14, 86);
            macroNameText.Name = "macroNameText";
            macroNameText.Size = new Size(320, 35);
            macroNameText.TabIndex = 2;
            // 
            // label1
            // 
            label1.AutoSize = true;
            label1.Location = new Point(14, 58);
            label1.Name = "label1";
            label1.Size = new Size(215, 30);
            label1.TabIndex = 3;
            label1.Text = "Macro Name (for file)";
            // 
            // statusLabel
            // 
            statusLabel.AutoSize = true;
            statusLabel.Location = new Point(210, 22);
            statusLabel.Name = "statusLabel";
            statusLabel.Size = new Size(129, 30);
            statusLabel.TabIndex = 4;
            statusLabel.Text = "Status: Idle";
            // 
            // commandsList
            // 
            commandsList.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
            commandsList.FormattingEnabled = true;
            commandsList.ItemHeight = 30;
            commandsList.Location = new Point(14, 172);
            commandsList.Name = "commandsList";
            commandsList.Size = new Size(500, 334);
            commandsList.TabIndex = 5;
            // 
            // MacroRecorderForm
            // 
            AutoScaleDimensions = new SizeF(12F, 30F);
            AutoScaleMode = AutoScaleMode.Font;
            ClientSize = new Size(530, 520);
            Controls.Add(commandsList);
            Controls.Add(statusLabel);
            Controls.Add(label1);
            Controls.Add(macroNameText);
            Controls.Add(saveButton);
            Controls.Add(startStopButton);
            Name = "MacroRecorderForm";
            Text = "Macro Recorder";
            ResumeLayout(false);
            PerformLayout();
        }

        #endregion

        private Button startStopButton;
        private Button saveButton;
        private TextBox macroNameText;
        private Label label1;
        private Label statusLabel;
        private ListBox commandsList;
    }
}
