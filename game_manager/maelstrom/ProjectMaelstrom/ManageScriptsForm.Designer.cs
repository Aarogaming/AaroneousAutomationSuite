namespace ProjectMaelstrom
{
    partial class ManageScriptsForm
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            scriptListBox = new ListBox();
            runScriptButton = new Button();
            stopScriptButton = new Button();
            refreshScriptsButton = new Button();
            importFromGithubButton = new Button();
            updateScriptButton = new Button();
            removeScriptButton = new Button();
            scriptStatusLabel = new Label();
            sourceLabel = new Label();
            loadLogButton = new Button();
            logPreviewLabel = new Label();
            logPreviewTextBox = new TextBox();
            dryRunCheckBox = new CheckBox();
            openScriptFolderButton = new Button();
            openFullLogButton = new Button();
            viewSourceButton = new Button();
            authorLabel = new Label();
            openLibraryRootButton = new Button();
            filterNoteLabel = new Label();
            provenanceLabel = new Label();
            simulationNoteLabel = new Label();
            primaryButtonsFlow = new FlowLayoutPanel();
            updateButtonsFlow = new FlowLayoutPanel();
            detailLayout = new TableLayoutPanel();
            splitContainer = new SplitContainer();
            SuspendLayout();
            // 
            // primaryButtonsFlow
            // 
            primaryButtonsFlow.AutoSize = true;
            primaryButtonsFlow.AutoSizeMode = AutoSizeMode.GrowAndShrink;
            primaryButtonsFlow.Dock = DockStyle.Top;
            primaryButtonsFlow.FlowDirection = FlowDirection.LeftToRight;
            primaryButtonsFlow.Margin = new Padding(0, 0, 0, 6);
            primaryButtonsFlow.WrapContents = false;
            // 
            // runScriptButton
            // 
            runScriptButton.AutoSize = true;
            runScriptButton.Location = new Point(0, 0);
            runScriptButton.Margin = new Padding(0, 0, 6, 0);
            runScriptButton.Name = "runScriptButton";
            runScriptButton.Size = new Size(140, 32);
            runScriptButton.TabIndex = 1;
            runScriptButton.Text = "Run";
            runScriptButton.UseVisualStyleBackColor = true;
            runScriptButton.Click += runScriptButton_Click;
            // 
            // stopScriptButton
            // 
            stopScriptButton.AutoSize = true;
            stopScriptButton.Location = new Point(146, 0);
            stopScriptButton.Margin = new Padding(0, 0, 6, 0);
            stopScriptButton.Name = "stopScriptButton";
            stopScriptButton.Size = new Size(140, 32);
            stopScriptButton.TabIndex = 2;
            stopScriptButton.Text = "Stop";
            stopScriptButton.UseVisualStyleBackColor = true;
            stopScriptButton.Click += stopScriptButton_Click;
            // 
            // refreshScriptsButton
            // 
            refreshScriptsButton.AutoSize = true;
            refreshScriptsButton.Location = new Point(292, 0);
            refreshScriptsButton.Margin = new Padding(0);
            refreshScriptsButton.Name = "refreshScriptsButton";
            refreshScriptsButton.Size = new Size(170, 32);
            refreshScriptsButton.TabIndex = 3;
            refreshScriptsButton.Text = "Refresh Library";
            refreshScriptsButton.UseVisualStyleBackColor = true;
            refreshScriptsButton.Click += refreshScriptsButton_Click;
            primaryButtonsFlow.Controls.Add(runScriptButton);
            primaryButtonsFlow.Controls.Add(stopScriptButton);
            primaryButtonsFlow.Controls.Add(refreshScriptsButton);
            // 
            // importFromGithubButton
            // 
            importFromGithubButton.AutoSize = true;
            importFromGithubButton.AutoSizeMode = AutoSizeMode.GrowAndShrink;
            importFromGithubButton.Dock = DockStyle.Top;
            importFromGithubButton.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            importFromGithubButton.Location = new Point(0, 38);
            importFromGithubButton.Margin = new Padding(0, 0, 0, 6);
            importFromGithubButton.MaximumSize = new Size(0, 32);
            importFromGithubButton.MinimumSize = new Size(200, 32);
            importFromGithubButton.Name = "importFromGithubButton";
            importFromGithubButton.Size = new Size(137, 32);
            importFromGithubButton.TabIndex = 4;
            importFromGithubButton.Text = "Add from GitHub";
            importFromGithubButton.UseVisualStyleBackColor = true;
            importFromGithubButton.Click += importFromGithubButton_Click;
            // 
            // updateButtonsFlow
            // 
            updateButtonsFlow.AutoSize = true;
            updateButtonsFlow.AutoSizeMode = AutoSizeMode.GrowAndShrink;
            updateButtonsFlow.Dock = DockStyle.Top;
            updateButtonsFlow.FlowDirection = FlowDirection.LeftToRight;
            updateButtonsFlow.Margin = new Padding(0, 0, 0, 8);
            updateButtonsFlow.WrapContents = false;
            // 
            // updateScriptButton
            // 
            updateScriptButton.AutoSize = true;
            updateScriptButton.Location = new Point(0, 0);
            updateScriptButton.Margin = new Padding(0, 0, 6, 0);
            updateScriptButton.Name = "updateScriptButton";
            updateScriptButton.Size = new Size(140, 28);
            updateScriptButton.TabIndex = 5;
            updateScriptButton.Text = "Update";
            updateScriptButton.UseVisualStyleBackColor = true;
            updateScriptButton.Click += updateScriptButton_Click;
            // 
            // removeScriptButton
            // 
            removeScriptButton.AutoSize = true;
            removeScriptButton.Location = new Point(146, 0);
            removeScriptButton.Margin = new Padding(0);
            removeScriptButton.Name = "removeScriptButton";
            removeScriptButton.Size = new Size(140, 28);
            removeScriptButton.TabIndex = 6;
            removeScriptButton.Text = "Remove";
            removeScriptButton.UseVisualStyleBackColor = true;
            removeScriptButton.Click += removeScriptButton_Click;
            updateButtonsFlow.Controls.Add(updateScriptButton);
            updateButtonsFlow.Controls.Add(removeScriptButton);
            // 
            // scriptStatusLabel
            // 
            scriptStatusLabel.AutoSize = true;
            scriptStatusLabel.Location = new Point(0, 0);
            scriptStatusLabel.Margin = new Padding(0, 0, 0, 2);
            scriptStatusLabel.Name = "scriptStatusLabel";
            scriptStatusLabel.Size = new Size(88, 20);
            scriptStatusLabel.TabIndex = 4;
            scriptStatusLabel.Text = "Status: Idle";
            // 
            // sourceLabel
            // 
            sourceLabel.AutoSize = true;
            sourceLabel.Location = new Point(0, 22);
            sourceLabel.Margin = new Padding(0, 0, 0, 2);
            sourceLabel.Name = "sourceLabel";
            sourceLabel.Size = new Size(69, 20);
            sourceLabel.TabIndex = 7;
            sourceLabel.Text = "Source: -";
            // 
            // authorLabel
            // 
            authorLabel.AutoSize = true;
            authorLabel.Location = new Point(0, 44);
            authorLabel.Margin = new Padding(0, 0, 0, 2);
            authorLabel.Name = "authorLabel";
            authorLabel.Size = new Size(68, 20);
            authorLabel.TabIndex = 15;
            authorLabel.Text = "Author: -";
            // 
            // provenanceLabel
            // 
            provenanceLabel.AutoSize = true;
            provenanceLabel.Location = new Point(0, 66);
            provenanceLabel.Margin = new Padding(0, 0, 0, 2);
            provenanceLabel.Name = "provenanceLabel";
            provenanceLabel.Size = new Size(157, 20);
            provenanceLabel.TabIndex = 16;
            provenanceLabel.Text = "Provenance / Credits: -";
            // 
            // filterNoteLabel
            // 
            filterNoteLabel.AutoSize = true;
            filterNoteLabel.Location = new Point(0, 88);
            filterNoteLabel.Margin = new Padding(0, 0, 0, 6);
            filterNoteLabel.Name = "filterNoteLabel";
            filterNoteLabel.Size = new Size(0, 20);
            filterNoteLabel.TabIndex = 17;
            filterNoteLabel.Text = "";
            filterNoteLabel.Visible = false;
            // 
            // simulationNoteLabel
            // 
            simulationNoteLabel.AutoSize = true;
            simulationNoteLabel.ForeColor = Color.Gold;
            simulationNoteLabel.Location = new Point(0, 0);
            simulationNoteLabel.Margin = new Padding(0, 0, 0, 6);
            simulationNoteLabel.Name = "simulationNoteLabel";
            simulationNoteLabel.Size = new Size(0, 20);
            simulationNoteLabel.TabIndex = 18;
            // 
            // loadLogButton
            // 
            loadLogButton.AutoSize = true;
            loadLogButton.Dock = DockStyle.Top;
            loadLogButton.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            loadLogButton.Location = new Point(0, 0);
            loadLogButton.Margin = new Padding(0, 0, 0, 4);
            loadLogButton.MinimumSize = new Size(120, 30);
            loadLogButton.Name = "loadLogButton";
            loadLogButton.Size = new Size(88, 30);
            loadLogButton.TabIndex = 8;
            loadLogButton.Text = "Load Log";
            loadLogButton.UseVisualStyleBackColor = true;
            loadLogButton.Click += loadLogButton_Click;
            // 
            // logPreviewLabel
            // 
            logPreviewLabel.AutoSize = true;
            logPreviewLabel.Location = new Point(0, 0);
            logPreviewLabel.Margin = new Padding(0, 0, 0, 2);
            logPreviewLabel.Name = "logPreviewLabel";
            logPreviewLabel.Size = new Size(84, 20);
            logPreviewLabel.TabIndex = 6;
            logPreviewLabel.Text = "Log Preview";
            // 
            // logPreviewTextBox
            // 
            logPreviewTextBox.Dock = DockStyle.Top;
            logPreviewTextBox.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            logPreviewTextBox.Location = new Point(0, 0);
            logPreviewTextBox.Margin = new Padding(0, 0, 0, 8);
            logPreviewTextBox.Multiline = true;
            logPreviewTextBox.Name = "logPreviewTextBox";
            logPreviewTextBox.ReadOnly = true;
            logPreviewTextBox.ScrollBars = ScrollBars.Vertical;
            logPreviewTextBox.Size = new Size(663, 240);
            logPreviewTextBox.TabIndex = 9;
            // 
            // dryRunCheckBox
            // 
            dryRunCheckBox.AutoSize = true;
            dryRunCheckBox.Location = new Point(0, 0);
            dryRunCheckBox.Margin = new Padding(0, 0, 0, 6);
            dryRunCheckBox.Name = "dryRunCheckBox";
            dryRunCheckBox.Size = new Size(77, 24);
            dryRunCheckBox.TabIndex = 10;
            dryRunCheckBox.Text = "Dry run";
            dryRunCheckBox.UseVisualStyleBackColor = true;
            dryRunCheckBox.CheckedChanged += dryRunCheckBox_CheckedChanged;
            // 
            // openScriptFolderButton
            // 
            openScriptFolderButton.AutoSize = true;
            openScriptFolderButton.Dock = DockStyle.Top;
            openScriptFolderButton.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            openScriptFolderButton.Location = new Point(0, 0);
            openScriptFolderButton.Margin = new Padding(0, 4, 0, 4);
            openScriptFolderButton.MinimumSize = new Size(200, 30);
            openScriptFolderButton.Name = "openScriptFolderButton";
            openScriptFolderButton.Size = new Size(96, 30);
            openScriptFolderButton.TabIndex = 12;
            openScriptFolderButton.Text = "Open Script Folder";
            openScriptFolderButton.UseVisualStyleBackColor = true;
            openScriptFolderButton.Click += openScriptFolderButton_Click;
            // 
            // openLibraryRootButton
            // 
            openLibraryRootButton.AutoSize = true;
            openLibraryRootButton.Dock = DockStyle.Top;
            openLibraryRootButton.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            openLibraryRootButton.Location = new Point(0, 0);
            openLibraryRootButton.Margin = new Padding(0, 0, 0, 4);
            openLibraryRootButton.MinimumSize = new Size(200, 30);
            openLibraryRootButton.Name = "openLibraryRootButton";
            openLibraryRootButton.Size = new Size(130, 30);
            openLibraryRootButton.TabIndex = 11;
            openLibraryRootButton.Text = "Open Script Library";
            openLibraryRootButton.UseVisualStyleBackColor = true;
            openLibraryRootButton.Click += openLibraryRootButton_Click;
            // 
            // viewSourceButton
            // 
            viewSourceButton.AutoSize = true;
            viewSourceButton.Dock = DockStyle.Top;
            viewSourceButton.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            viewSourceButton.Location = new Point(0, 0);
            viewSourceButton.Margin = new Padding(0, 0, 0, 4);
            viewSourceButton.MinimumSize = new Size(200, 30);
            viewSourceButton.Name = "viewSourceButton";
            viewSourceButton.Size = new Size(152, 30);
            viewSourceButton.TabIndex = 14;
            viewSourceButton.Text = "View Source (GitHub)";
            viewSourceButton.UseVisualStyleBackColor = true;
            viewSourceButton.Click += viewSourceButton_Click;
            // 
            // openFullLogButton
            // 
            openFullLogButton.AutoSize = true;
            openFullLogButton.Dock = DockStyle.Top;
            openFullLogButton.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            openFullLogButton.Location = new Point(0, 0);
            openFullLogButton.Margin = new Padding(0, 0, 0, 0);
            openFullLogButton.MinimumSize = new Size(200, 30);
            openFullLogButton.Name = "openFullLogButton";
            openFullLogButton.Size = new Size(110, 30);
            openFullLogButton.TabIndex = 13;
            openFullLogButton.Text = "Open Full Log";
            openFullLogButton.UseVisualStyleBackColor = true;
            openFullLogButton.Click += openFullLogButton_Click;
            // 
            // scriptListBox
            // 
            scriptListBox.Dock = DockStyle.Fill;
            scriptListBox.FormattingEnabled = true;
            scriptListBox.HorizontalScrollbar = true;
            scriptListBox.IntegralHeight = false;
            scriptListBox.ItemHeight = 20;
            scriptListBox.Location = new Point(0, 0);
            scriptListBox.Name = "scriptListBox";
            scriptListBox.Size = new Size(513, 744);
            scriptListBox.TabIndex = 0;
            // 
            // detailLayout
            // 
            detailLayout.AutoScroll = true;
            detailLayout.ColumnCount = 1;
            detailLayout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100F));
            detailLayout.Controls.Add(simulationNoteLabel, 0, 0);
            detailLayout.Controls.Add(primaryButtonsFlow, 0, 1);
            detailLayout.Controls.Add(importFromGithubButton, 0, 2);
            detailLayout.Controls.Add(updateButtonsFlow, 0, 3);
            detailLayout.Controls.Add(scriptStatusLabel, 0, 4);
            detailLayout.Controls.Add(sourceLabel, 0, 5);
            detailLayout.Controls.Add(authorLabel, 0, 6);
            detailLayout.Controls.Add(provenanceLabel, 0, 7);
            detailLayout.Controls.Add(filterNoteLabel, 0, 8);
            detailLayout.Controls.Add(loadLogButton, 0, 9);
            detailLayout.Controls.Add(logPreviewLabel, 0, 10);
            detailLayout.Controls.Add(logPreviewTextBox, 0, 11);
            detailLayout.Controls.Add(dryRunCheckBox, 0, 12);
            detailLayout.Controls.Add(openScriptFolderButton, 0, 13);
            detailLayout.Controls.Add(openLibraryRootButton, 0, 14);
            detailLayout.Controls.Add(viewSourceButton, 0, 15);
            detailLayout.Controls.Add(openFullLogButton, 0, 16);
            detailLayout.Dock = DockStyle.Fill;
            detailLayout.Location = new Point(0, 0);
            detailLayout.Name = "detailLayout";
            detailLayout.Padding = new Padding(6);
            detailLayout.RowCount = 17;
            detailLayout.RowStyles.Add(new RowStyle());
            detailLayout.RowStyles.Add(new RowStyle());
            detailLayout.RowStyles.Add(new RowStyle());
            detailLayout.RowStyles.Add(new RowStyle());
            detailLayout.RowStyles.Add(new RowStyle());
            detailLayout.RowStyles.Add(new RowStyle());
            detailLayout.RowStyles.Add(new RowStyle());
            detailLayout.RowStyles.Add(new RowStyle());
            detailLayout.RowStyles.Add(new RowStyle());
            detailLayout.RowStyles.Add(new RowStyle());
            detailLayout.RowStyles.Add(new RowStyle());
            detailLayout.RowStyles.Add(new RowStyle(SizeType.Absolute, 250F));
            detailLayout.RowStyles.Add(new RowStyle());
            detailLayout.RowStyles.Add(new RowStyle());
            detailLayout.RowStyles.Add(new RowStyle());
            detailLayout.RowStyles.Add(new RowStyle());
            detailLayout.RowStyles.Add(new RowStyle());
            detailLayout.Size = new Size(675, 744);
            detailLayout.TabIndex = 19;
            // 
            // splitContainer
            // 
            splitContainer.Dock = DockStyle.Fill;
            splitContainer.Location = new Point(0, 0);
            splitContainer.Name = "splitContainer";
            splitContainer.Panel1.Controls.Add(scriptListBox);
            splitContainer.Panel1.Padding = new Padding(6, 8, 6, 8);
            splitContainer.Panel1MinSize = 0;
            splitContainer.Panel2.Controls.Add(detailLayout);
            splitContainer.Panel2.Padding = new Padding(6, 8, 6, 8);
            splitContainer.Panel2MinSize = 0;
            splitContainer.Size = new Size(1200, 760);
            splitContainer.SplitterDistance = 600;
            splitContainer.TabIndex = 0;
            // 
            // ManageScriptsForm
            // 
            AutoScaleDimensions = new SizeF(8F, 20F);
            AutoScaleMode = AutoScaleMode.Font;
            ClientSize = new Size(1200, 760);
            Controls.Add(splitContainer);
            Name = "ManageScriptsForm";
            Text = "Manage Scripts";
            Load += ManageScriptsForm_Load;
            ResumeLayout(false);
        }

        #endregion

        private ListBox scriptListBox;
        private Button runScriptButton;
        private Button stopScriptButton;
        private Button refreshScriptsButton;
        private Label scriptStatusLabel;
        private Button loadLogButton;
        private Label logPreviewLabel;
        private TextBox logPreviewTextBox;
        private CheckBox dryRunCheckBox;
        private Button openScriptFolderButton;
        private Button openFullLogButton;
        private Button viewSourceButton;
        private Button openLibraryRootButton;
        private Button importFromGithubButton;
        private Button updateScriptButton;
        private Button removeScriptButton;
        private Label sourceLabel;
        private Label authorLabel;
        private Label filterNoteLabel;
        private Label provenanceLabel;
        private Label simulationNoteLabel;
        private FlowLayoutPanel primaryButtonsFlow;
        private FlowLayoutPanel updateButtonsFlow;
        private TableLayoutPanel detailLayout;
        private SplitContainer splitContainer;
    }
}
