namespace ProjectMaelstrom
{
    partial class AboutForm
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
            creditsTextBox = new TextBox();
            closeButton = new Button();
            SuspendLayout();
            // 
            // creditsTextBox
            // 
            creditsTextBox.Location = new Point(12, 12);
            creditsTextBox.Multiline = true;
            creditsTextBox.Name = "creditsTextBox";
            creditsTextBox.ReadOnly = true;
            creditsTextBox.ScrollBars = ScrollBars.Vertical;
            creditsTextBox.Size = new Size(460, 260);
            creditsTextBox.TabIndex = 0;
            // 
            // closeButton
            // 
            closeButton.Anchor = AnchorStyles.Bottom | AnchorStyles.Right;
            closeButton.Location = new Point(372, 280);
            closeButton.Name = "closeButton";
            closeButton.Size = new Size(100, 30);
            closeButton.TabIndex = 1;
            closeButton.Text = "Close";
            closeButton.UseVisualStyleBackColor = true;
            closeButton.Click += closeButton_Click;
            // 
            // AboutForm
            // 
            AutoScaleDimensions = new SizeF(8F, 20F);
            AutoScaleMode = AutoScaleMode.Font;
            ClientSize = new Size(484, 322);
            Controls.Add(closeButton);
            Controls.Add(creditsTextBox);
            Name = "AboutForm";
            StartPosition = FormStartPosition.CenterParent;
            Text = "About Project Maelstrom";
            Load += AboutForm_Load;
            ResumeLayout(false);
            PerformLayout();
        }

        #endregion

        private TextBox creditsTextBox = null!;
        private Button closeButton = null!;
    }
}
