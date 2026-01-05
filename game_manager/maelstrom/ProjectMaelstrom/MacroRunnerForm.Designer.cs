namespace ProjectMaelstrom
{
    partial class MacroRunnerForm
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
            macroList = new ListBox();
            runButton = new Button();
            refreshButton = new Button();
            statusLabel = new Label();
            SuspendLayout();
            // 
            // macroList
            // 
            macroList.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
            macroList.FormattingEnabled = true;
            macroList.ItemHeight = 30;
            macroList.Location = new Point(14, 14);
            macroList.Name = "macroList";
            macroList.Size = new Size(420, 304);
            macroList.TabIndex = 0;
            // 
            // runButton
            // 
            runButton.Anchor = AnchorStyles.Bottom | AnchorStyles.Left;
            runButton.Location = new Point(14, 334);
            runButton.Name = "runButton";
            runButton.Size = new Size(160, 38);
            runButton.TabIndex = 1;
            runButton.Text = "Run";
            runButton.UseVisualStyleBackColor = true;
            runButton.Click += runButton_Click;
            // 
            // refreshButton
            // 
            refreshButton.Anchor = AnchorStyles.Bottom | AnchorStyles.Left;
            refreshButton.Location = new Point(180, 334);
            refreshButton.Name = "refreshButton";
            refreshButton.Size = new Size(160, 38);
            refreshButton.TabIndex = 2;
            refreshButton.Text = "Refresh";
            refreshButton.UseVisualStyleBackColor = true;
            refreshButton.Click += refreshButton_Click;
            // 
            // statusLabel
            // 
            statusLabel.Anchor = AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
            statusLabel.AutoSize = true;
            statusLabel.Location = new Point(14, 382);
            statusLabel.Name = "statusLabel";
            statusLabel.Size = new Size(92, 30);
            statusLabel.TabIndex = 3;
            statusLabel.Text = "Status: -";
            // 
            // MacroRunnerForm
            // 
            AutoScaleDimensions = new SizeF(12F, 30F);
            AutoScaleMode = AutoScaleMode.Font;
            ClientSize = new Size(452, 420);
            Controls.Add(statusLabel);
            Controls.Add(refreshButton);
            Controls.Add(runButton);
            Controls.Add(macroList);
            Name = "MacroRunnerForm";
            Text = "Macro Runner";
            Load += MacroRunnerForm_Load;
            ResumeLayout(false);
            PerformLayout();
        }

        #endregion

        private ListBox macroList;
        private Button runButton;
        private Button refreshButton;
        private Label statusLabel;
    }
}
