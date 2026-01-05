namespace ProjectMaelstrom
{
    partial class MapViewerForm
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
            worldCombo = new ComboBox();
            zoneList = new ListBox();
            mapPicture = new PictureBox();
            statusLabel = new Label();
            refreshButton = new Button();
            ((System.ComponentModel.ISupportInitialize)mapPicture).BeginInit();
            SuspendLayout();
            // 
            // worldCombo
            // 
            worldCombo.DropDownStyle = ComboBoxStyle.DropDownList;
            worldCombo.FormattingEnabled = true;
            worldCombo.Location = new Point(12, 12);
            worldCombo.Name = "worldCombo";
            worldCombo.Size = new Size(240, 28);
            worldCombo.TabIndex = 0;
            worldCombo.SelectedIndexChanged += worldCombo_SelectedIndexChanged;
            // 
            // zoneList
            // 
            zoneList.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left;
            zoneList.FormattingEnabled = true;
            zoneList.ItemHeight = 20;
            zoneList.Location = new Point(12, 50);
            zoneList.Name = "zoneList";
            zoneList.Size = new Size(240, 384);
            zoneList.TabIndex = 1;
            zoneList.SelectedIndexChanged += zoneList_SelectedIndexChanged;
            // 
            // mapPicture
            // 
            mapPicture.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
            mapPicture.Location = new Point(264, 12);
            mapPicture.Name = "mapPicture";
            mapPicture.Size = new Size(640, 458);
            mapPicture.SizeMode = PictureBoxSizeMode.Zoom;
            mapPicture.TabIndex = 2;
            mapPicture.TabStop = false;
            // 
            // statusLabel
            // 
            statusLabel.Anchor = AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
            statusLabel.Location = new Point(12, 447);
            statusLabel.Name = "statusLabel";
            statusLabel.Size = new Size(892, 23);
            statusLabel.TabIndex = 3;
            statusLabel.Text = "Status: Idle";
            // 
            // refreshButton
            // 
            refreshButton.Location = new Point(764, 476);
            refreshButton.Name = "refreshButton";
            refreshButton.Size = new Size(140, 32);
            refreshButton.TabIndex = 4;
            refreshButton.Text = "Refresh Zones";
            refreshButton.UseVisualStyleBackColor = true;
            refreshButton.Click += refreshButton_Click;
            // 
            // MapViewerForm
            // 
            AutoScaleDimensions = new SizeF(8F, 20F);
            AutoScaleMode = AutoScaleMode.Font;
            ClientSize = new Size(916, 520);
            Controls.Add(refreshButton);
            Controls.Add(statusLabel);
            Controls.Add(mapPicture);
            Controls.Add(zoneList);
            Controls.Add(worldCombo);
            Name = "MapViewerForm";
            Text = "World Maps";
            Load += MapViewerForm_Load;
            ((System.ComponentModel.ISupportInitialize)mapPicture).EndInit();
            ResumeLayout(false);
        }

        #endregion

        private ComboBox worldCombo;
        private ListBox zoneList;
        private PictureBox mapPicture;
        private Label statusLabel;
        private Button refreshButton;
    }
}
