namespace ProjectMaelstrom
{
    partial class SettingsForm
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
            label1 = new Label();
            ocrSpaceApiKey = new TextBox();
            saveSettingsBtn = new Button();
            label2 = new Label();
            selectedGameResolution = new ComboBox();
            themeModeLabel = new Label();
            themeModeCombo = new ComboBox();
            captureToggle = new CheckBox();
            audioToggle = new CheckBox();
            tuningToggle = new CheckBox();
            devTelemetryToggle = new CheckBox();
            devUiSnapshotsToggle = new CheckBox();
            captureUiSnapshotButton = new Button();
            playerPreviewToggle = new CheckBox();
            autoPauseToggle = new CheckBox();
            audioDeltaLabel = new Label();
            audioDeltaNumeric = new NumericUpDown();
            updatesLabel = new Label();
            feedUrlText = new TextBox();
            autoCheckUpdatesToggle = new CheckBox();
            checkUpdatesButton = new Button();
            downloadUpdateButton = new Button();
            applyUpdateButton = new Button();
            updaterStatusLabel = new Label();
            launchManagerButton = new Button();
            openMapViewerButton = new Button();
            refreshWikiButton = new Button();
            runDiagnosticsButton = new Button();
            viewDevSuggestionsButton = new Button();
            goldMinLabel = new Label();
            goldMinNumeric = new NumericUpDown();
            goldCapLabel = new Label();
            goldCapNumeric = new NumericUpDown();
            devOptionsLabel = new Label();
            policyAllowLabel = new Label();
            policyModeLabel = new Label();
            policyPathLabel = new Label();
            policyLoadedLabel = new Label();
            openPolicyFolderButton = new Button();
            policyBackendLabel = new Label();
            policyBackendIdLabel = new Label();
            pluginsLabel = new Label();
            pluginListView = new ListView();
            pluginColumn = new ColumnHeader();
            versionColumn = new ColumnHeader();
            capabilitiesColumn = new ColumnHeader();
            statusColumn = new ColumnHeader();
            reasonColumn = new ColumnHeader();
            openPluginsFolderButton = new Button();
            reloadPluginsButton = new Button();
            installSamplesButton = new Button();
            removeSamplesButton = new Button();
            replaysLabel = new Label();
            replayListView = new ListView();
            replayNameColumn = new ColumnHeader();
            replayDateColumn = new ColumnHeader();
            openReplaysFolderButton = new Button();
            refreshReplaysButton = new Button();
            replayDetailsBox = new TextBox();
            installFromGithubButton = new Button();
            pluginInstallStatusLabel = new Label();
            overlayWidgetsLabel = new Label();
            overlayFlowPanel = new FlowLayoutPanel();
            overlayEmptyLabel = new Label();
            overlayListBox = new ListBox();
            overlayHostPanel = new Panel();
            overlayStatusLabel = new Label();
            minigamesLabel = new Label();
            minigameFiltersFlow = new FlowLayoutPanel();
            minigameCategoryFilterLabel = new Label();
            minigameCategoryFilter = new ComboBox();
            minigameStatusFilterLabel = new Label();
            minigameStatusFilter = new ComboBox();
            minigameListView = new ListView();
            minigameNameColumn = new ColumnHeader();
            minigameCategoryColumn = new ColumnHeader();
            minigameStatusColumn = new ColumnHeader();
            minigameTagsColumn = new ColumnHeader();
            minigamePluginColumn = new ColumnHeader();
            minigameDetailsBox = new TextBox();
            pluginButtonsFlow = new FlowLayoutPanel();
            replayButtonsFlow = new FlowLayoutPanel();
            overlayLayout = new FlowLayoutPanel();
            devLayout = new TableLayoutPanel();
            ((System.ComponentModel.ISupportInitialize)audioDeltaNumeric).BeginInit();
            ((System.ComponentModel.ISupportInitialize)goldMinNumeric).BeginInit();
            ((System.ComponentModel.ISupportInitialize)goldCapNumeric).BeginInit();
            SuspendLayout();
            // 
            // label1
            // 
            label1.AutoSize = true;
            label1.Location = new Point(14, 11);
            label1.Name = "label1";
            label1.Size = new Size(193, 30);
            label1.TabIndex = 0;
            label1.Text = "OCR Space API Key";
            // 
            // ocrSpaceApiKey
            // 
            ocrSpaceApiKey.Location = new Point(14, 44);
            ocrSpaceApiKey.Name = "ocrSpaceApiKey";
            ocrSpaceApiKey.Size = new Size(359, 35);
            ocrSpaceApiKey.TabIndex = 1;
            // 
            // saveSettingsBtn
            // 
            saveSettingsBtn.Location = new Point(13, 544);
            saveSettingsBtn.Name = "saveSettingsBtn";
            saveSettingsBtn.Size = new Size(360, 41);
            saveSettingsBtn.TabIndex = 4;
            saveSettingsBtn.Text = "Save";
            saveSettingsBtn.UseVisualStyleBackColor = true;
            saveSettingsBtn.Click += saveSettingsBtn_Click;
            // 
            // label2
            // 
            label2.AutoSize = true;
            label2.Location = new Point(12, 95);
            label2.Name = "label2";
            label2.Size = new Size(231, 30);
            label2.TabIndex = 5;
            label2.Text = "Select Game Resolution";
            // 
            // selectedGameResolution
            // 
            selectedGameResolution.FormattingEnabled = true;
            selectedGameResolution.Items.AddRange(new object[] { "1280x720" });
            selectedGameResolution.Location = new Point(14, 133);
            selectedGameResolution.Name = "selectedGameResolution";
            selectedGameResolution.Size = new Size(359, 38);
            selectedGameResolution.TabIndex = 6;
            selectedGameResolution.Text = "1280x720";
            // 
            // themeModeLabel
            // 
            themeModeLabel.AutoSize = true;
            themeModeLabel.Location = new Point(14, 183);
            themeModeLabel.Name = "themeModeLabel";
            themeModeLabel.Size = new Size(124, 30);
            themeModeLabel.TabIndex = 7;
            themeModeLabel.Text = "Theme Mode";
            // 
            // themeModeCombo
            // 
            themeModeCombo.DropDownStyle = ComboBoxStyle.DropDownList;
            themeModeCombo.FormattingEnabled = true;
            themeModeCombo.Items.AddRange(new object[] { "System", "Wizard101" });
            themeModeCombo.Location = new Point(14, 220);
            themeModeCombo.Name = "themeModeCombo";
            themeModeCombo.Size = new Size(359, 38);
            themeModeCombo.TabIndex = 8;
            // 
            // captureToggle
            // 
            captureToggle.AutoSize = true;
            captureToggle.Location = new Point(14, 270);
            captureToggle.Name = "captureToggle";
            captureToggle.Size = new Size(270, 34);
            captureToggle.TabIndex = 9;
            captureToggle.Text = "Enable Dev Screen Capture";
            captureToggle.UseVisualStyleBackColor = true;
            // 
            // audioToggle
            // 
            audioToggle.AutoSize = true;
            audioToggle.Location = new Point(14, 308);
            audioToggle.Name = "audioToggle";
            audioToggle.Size = new Size(233, 34);
            audioToggle.TabIndex = 10;
            audioToggle.Text = "Enable Audio Recognizer";
            audioToggle.UseVisualStyleBackColor = true;
            // 
            // tuningToggle
            // 
            tuningToggle.AutoSize = true;
            tuningToggle.Location = new Point(14, 346);
            tuningToggle.Name = "tuningToggle";
            tuningToggle.Size = new Size(241, 34);
            tuningToggle.TabIndex = 11;
            tuningToggle.Text = "Enable SmartPlay Tuning";
            tuningToggle.UseVisualStyleBackColor = true;
            // 
            // devTelemetryToggle
            // 
            devTelemetryToggle.AutoSize = true;
            devTelemetryToggle.Location = new Point(14, 422);
            devTelemetryToggle.Name = "devTelemetryToggle";
            devTelemetryToggle.Size = new Size(329, 34);
            devTelemetryToggle.TabIndex = 12;
            devTelemetryToggle.Text = "Capture Dev Telemetry (logs only)";
            devTelemetryToggle.UseVisualStyleBackColor = true;
            // 
            // devUiSnapshotsToggle
            // 
            devUiSnapshotsToggle.AutoSize = true;
            devUiSnapshotsToggle.Location = new Point(14, 460);
            devUiSnapshotsToggle.Name = "devUiSnapshotsToggle";
            devUiSnapshotsToggle.Size = new Size(296, 34);
            devUiSnapshotsToggle.TabIndex = 13;
            devUiSnapshotsToggle.Text = "Enable Dev UI Snapshots";
            devUiSnapshotsToggle.UseVisualStyleBackColor = true;
            // 
            // captureUiSnapshotButton
            // 
            captureUiSnapshotButton.Location = new Point(14, 500);
            captureUiSnapshotButton.Name = "captureUiSnapshotButton";
            captureUiSnapshotButton.Size = new Size(478, 34);
            captureUiSnapshotButton.TabIndex = 14;
            captureUiSnapshotButton.Text = "Capture UI Snapshot (Dev)";
            captureUiSnapshotButton.UseVisualStyleBackColor = true;
            captureUiSnapshotButton.Visible = false;
            captureUiSnapshotButton.Click += captureUiSnapshotButton_Click;
            // 
            // playerPreviewToggle
            // 
            playerPreviewToggle.AutoSize = true;
            playerPreviewToggle.Location = new Point(14, 542);
            playerPreviewToggle.Name = "playerPreviewToggle";
            playerPreviewToggle.Size = new Size(270, 34);
            playerPreviewToggle.TabIndex = 15;
            playerPreviewToggle.Text = "Player Mode (Preview UI)";
            playerPreviewToggle.UseVisualStyleBackColor = true;
            playerPreviewToggle.Visible = false;
            // 
            // autoPauseToggle
            // 
            autoPauseToggle.AutoSize = true;
            autoPauseToggle.Location = new Point(14, 580);
            autoPauseToggle.Name = "autoPauseToggle";
            autoPauseToggle.Size = new Size(321, 34);
            autoPauseToggle.TabIndex = 16;
            autoPauseToggle.Text = "Auto-pause SmartPlay on focus loss";
            autoPauseToggle.UseVisualStyleBackColor = true;
            // 
            // audioDeltaLabel
            // 
            audioDeltaLabel.AutoSize = true;
            audioDeltaLabel.Location = new Point(200, 312);
            audioDeltaLabel.Name = "audioDeltaLabel";
            audioDeltaLabel.Size = new Size(166, 30);
            audioDeltaLabel.TabIndex = 12;
            audioDeltaLabel.Text = "Audio Sensitivity";
            // 
            // audioDeltaNumeric
            // 
            audioDeltaNumeric.DecimalPlaces = 2;
            audioDeltaNumeric.Increment = new decimal(new int[] { 1, 0, 0, 131072 });
            audioDeltaNumeric.Location = new Point(372, 308);
            audioDeltaNumeric.Maximum = new decimal(new int[] { 50, 0, 0, 131072 });
            audioDeltaNumeric.Minimum = new decimal(new int[] { 1, 0, 0, 196608 });
            audioDeltaNumeric.Name = "audioDeltaNumeric";
            audioDeltaNumeric.Size = new Size(120, 35);
            audioDeltaNumeric.TabIndex = 15;
            audioDeltaNumeric.Value = new decimal(new int[] { 12, 0, 0, 131072 });
            // 
            // goldMinLabel
            // 
            goldMinLabel.AutoSize = true;
            goldMinLabel.Location = new Point(14, 620);
            goldMinLabel.Name = "goldMinLabel";
            goldMinLabel.Size = new Size(229, 30);
            goldMinLabel.TabIndex = 26;
            goldMinLabel.Text = "Bazaar Gold Min (stop)";
            // 
            // goldMinNumeric
            // 
            goldMinNumeric.Increment = new decimal(new int[] { 1000, 0, 0, 0 });
            goldMinNumeric.Maximum = new decimal(new int[] { 1000000, 0, 0, 0 });
            goldMinNumeric.Location = new Point(260, 616);
            goldMinNumeric.Name = "goldMinNumeric";
            goldMinNumeric.Size = new Size(232, 35);
            goldMinNumeric.TabIndex = 27;
            // 
            // goldCapLabel
            // 
            goldCapLabel.AutoSize = true;
            goldCapLabel.Location = new Point(14, 662);
            goldCapLabel.Name = "goldCapLabel";
            goldCapLabel.Size = new Size(228, 30);
            goldCapLabel.TabIndex = 28;
            goldCapLabel.Text = "Bazaar Gold Cap (pause)";
            // 
            // goldCapNumeric
            // 
            goldCapNumeric.Increment = new decimal(new int[] { 1000, 0, 0, 0 });
            goldCapNumeric.Maximum = new decimal(new int[] { 1000000, 0, 0, 0 });
            goldCapNumeric.Location = new Point(260, 658);
            goldCapNumeric.Name = "goldCapNumeric";
            goldCapNumeric.Size = new Size(232, 35);
            goldCapNumeric.TabIndex = 29;
            // 
            // devOptionsLabel
            // 
            devOptionsLabel.AutoSize = true;
            devOptionsLabel.Font = new Font("Segoe UI", 10F, FontStyle.Bold, GraphicsUnit.Point);
            devOptionsLabel.Margin = new Padding(0, 0, 0, 6);
            devOptionsLabel.Location = new Point(520, 14);
            devOptionsLabel.Name = "devOptionsLabel";
            devOptionsLabel.Size = new Size(164, 28);
            devOptionsLabel.TabIndex = 30;
            devOptionsLabel.Text = "Developer Options";
            // 
            // policyAllowLabel
            // 
            policyAllowLabel.AutoSize = true;
            policyAllowLabel.Location = new Point(520, 52);
            policyAllowLabel.MaximumSize = new Size(780, 0);
            policyAllowLabel.Name = "policyAllowLabel";
            policyAllowLabel.Size = new Size(120, 30);
            policyAllowLabel.TabIndex = 31;
            policyAllowLabel.Text = "Allow Live: -";
            // 
            // policyModeLabel
            // 
            policyModeLabel.AutoSize = true;
            policyModeLabel.Location = new Point(520, 86);
            policyModeLabel.MaximumSize = new Size(780, 0);
            policyModeLabel.Name = "policyModeLabel";
            policyModeLabel.Size = new Size(104, 30);
            policyModeLabel.TabIndex = 32;
            policyModeLabel.Text = "Mode: -";
            // 
            // policyPathLabel
            // 
            policyPathLabel.AutoSize = true;
            policyPathLabel.Location = new Point(520, 120);
            policyPathLabel.MaximumSize = new Size(780, 0);
            policyPathLabel.Name = "policyPathLabel";
            policyPathLabel.Size = new Size(74, 30);
            policyPathLabel.TabIndex = 33;
            policyPathLabel.Text = "Path: -";
            // 
            // policyLoadedLabel
            // 
            policyLoadedLabel.AutoSize = true;
            policyLoadedLabel.Location = new Point(520, 154);
            policyLoadedLabel.MaximumSize = new Size(780, 0);
            policyLoadedLabel.Name = "policyLoadedLabel";
            policyLoadedLabel.Size = new Size(110, 30);
            policyLoadedLabel.TabIndex = 34;
            policyLoadedLabel.Text = "Loaded: -";
            // 
            // openPolicyFolderButton
            // 
            openPolicyFolderButton.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            openPolicyFolderButton.Location = new Point(520, 190);
            openPolicyFolderButton.Margin = new Padding(0, 4, 0, 6);
            openPolicyFolderButton.Name = "openPolicyFolderButton";
            openPolicyFolderButton.Size = new Size(200, 34);
            openPolicyFolderButton.TabIndex = 35;
            openPolicyFolderButton.Text = "Open Policy Folder";
            openPolicyFolderButton.UseVisualStyleBackColor = true;
            openPolicyFolderButton.Click += openPolicyFolderButton_Click;
            // 
            // policyBackendLabel
            // 
            policyBackendLabel.AutoSize = true;
            policyBackendLabel.Location = new Point(520, 230);
            policyBackendLabel.MaximumSize = new Size(780, 0);
            policyBackendLabel.Name = "policyBackendLabel";
            policyBackendLabel.Size = new Size(140, 30);
            policyBackendLabel.TabIndex = 36;
            policyBackendLabel.Text = "Live backend: -";
            // 
            // policyBackendIdLabel
            // 
            policyBackendIdLabel.AutoSize = true;
            policyBackendIdLabel.Location = new Point(520, 264);
            policyBackendIdLabel.MaximumSize = new Size(780, 0);
            policyBackendIdLabel.Name = "policyBackendIdLabel";
            policyBackendIdLabel.Size = new Size(101, 30);
            policyBackendIdLabel.TabIndex = 37;
            policyBackendIdLabel.Text = "Backend: -";
            // 
            // pluginsLabel
            // 
            pluginsLabel.AutoSize = true;
            pluginsLabel.Font = new Font("Segoe UI", 10F, FontStyle.Bold, GraphicsUnit.Point);
            pluginsLabel.Margin = new Padding(0, 6, 0, 4);
            pluginsLabel.Location = new Point(520, 300);
            pluginsLabel.Name = "pluginsLabel";
            pluginsLabel.Size = new Size(77, 28);
            pluginsLabel.TabIndex = 38;
            pluginsLabel.Text = "Plugins";
            // 
            // pluginListView
            // 
            pluginListView.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            pluginListView.Columns.AddRange(new ColumnHeader[] { pluginColumn, versionColumn, capabilitiesColumn, statusColumn, reasonColumn });
            pluginListView.FullRowSelect = true;
            pluginListView.GridLines = true;
            pluginListView.Location = new Point(520, 332);
            pluginListView.Margin = new Padding(0, 4, 0, 4);
            pluginListView.Name = "pluginListView";
            pluginListView.Size = new Size(780, 200);
            pluginListView.TabIndex = 39;
            pluginListView.UseCompatibleStateImageBehavior = false;
            pluginListView.View = View.Details;
            pluginListView.MultiSelect = false;
            // 
            // pluginColumn
            // 
            pluginColumn.Text = "Plugin";
            pluginColumn.Width = 140;
            // 
            // versionColumn
            // 
            versionColumn.Text = "Version";
            versionColumn.Width = 90;
            // 
            // capabilitiesColumn
            // 
            capabilitiesColumn.Text = "Capabilities";
            capabilitiesColumn.Width = 160;
            // 
            // statusColumn
            // 
            statusColumn.Text = "Status";
            statusColumn.Width = 120;
            // 
            // reasonColumn
            // 
            reasonColumn.Text = "Reason";
            reasonColumn.Width = 180;
            // 
            // openPluginsFolderButton
            // 
            openPluginsFolderButton.Location = new Point(520, 540);
            openPluginsFolderButton.Name = "openPluginsFolderButton";
            openPluginsFolderButton.Size = new Size(170, 34);
            openPluginsFolderButton.TabIndex = 40;
            openPluginsFolderButton.Text = "Open Plugins Folder";
            openPluginsFolderButton.UseVisualStyleBackColor = true;
            openPluginsFolderButton.Click += openPluginsFolderButton_Click;
            // 
            // reloadPluginsButton
            // 
            reloadPluginsButton.Location = new Point(700, 540);
            reloadPluginsButton.Name = "reloadPluginsButton";
            reloadPluginsButton.Size = new Size(140, 34);
            reloadPluginsButton.TabIndex = 41;
            reloadPluginsButton.Text = "Reload Plugins";
            reloadPluginsButton.UseVisualStyleBackColor = true;
            reloadPluginsButton.Click += reloadPluginsButton_Click;
            // 
            // installSamplesButton
            // 
            installSamplesButton.Location = new Point(850, 540);
            installSamplesButton.Name = "installSamplesButton";
            installSamplesButton.Size = new Size(150, 34);
            installSamplesButton.TabIndex = 42;
            installSamplesButton.Text = "Install Sample Plugins";
            installSamplesButton.UseVisualStyleBackColor = true;
            installSamplesButton.Click += installSamplesButton_Click;
            // 
            // removeSamplesButton
            // 
            removeSamplesButton.Location = new Point(1010, 540);
            removeSamplesButton.Name = "removeSamplesButton";
            removeSamplesButton.Size = new Size(160, 34);
            removeSamplesButton.TabIndex = 43;
            removeSamplesButton.Text = "Remove Sample Plugins";
            removeSamplesButton.UseVisualStyleBackColor = true;
            removeSamplesButton.Click += removeSamplesButton_Click;
            // 
            // installFromGithubButton
            // 
            installFromGithubButton.Location = new Point(1240, 540);
            installFromGithubButton.Name = "installFromGithubButton";
            installFromGithubButton.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            installFromGithubButton.AutoSize = true;
            installFromGithubButton.AutoSizeMode = AutoSizeMode.GrowAndShrink;
            installFromGithubButton.Margin = new Padding(0, 0, 0, 8);
            installFromGithubButton.Size = new Size(180, 34);
            installFromGithubButton.TabIndex = 44;
            installFromGithubButton.Text = "Install from GitHub Release...";
            installFromGithubButton.UseVisualStyleBackColor = true;
            installFromGithubButton.Click += installFromGithubButton_Click;
            // 
            // pluginInstallStatusLabel
            // 
            pluginInstallStatusLabel.AutoSize = true;
            pluginInstallStatusLabel.Location = new Point(520, 510);
            pluginInstallStatusLabel.MaximumSize = new Size(780, 0);
            pluginInstallStatusLabel.Margin = new Padding(0, 0, 0, 4);
            pluginInstallStatusLabel.Name = "pluginInstallStatusLabel";
            pluginInstallStatusLabel.Size = new Size(0, 30);
            pluginInstallStatusLabel.TabIndex = 45;
            // 
            // overlayWidgetsLabel
            // 
            overlayWidgetsLabel.AutoSize = true;
            overlayWidgetsLabel.Font = new Font("Segoe UI", 10F, FontStyle.Bold, GraphicsUnit.Point);
            overlayWidgetsLabel.Margin = new Padding(0, 6, 0, 4);
            overlayWidgetsLabel.Location = new Point(520, 950);
            overlayWidgetsLabel.Name = "overlayWidgetsLabel";
            overlayWidgetsLabel.Size = new Size(150, 28);
            overlayWidgetsLabel.TabIndex = 49;
            overlayWidgetsLabel.Text = "Overlay Preview";
            // 
            // overlayFlowPanel
            // 
            overlayFlowPanel.AutoScroll = true;
            overlayFlowPanel.Location = new Point(520, 982);
            overlayFlowPanel.Name = "overlayFlowPanel";
            overlayFlowPanel.Size = new Size(620, 180);
            overlayFlowPanel.TabIndex = 50;
            // 
            // overlayEmptyLabel
            // 
            overlayEmptyLabel.AutoSize = true;
            overlayEmptyLabel.Location = new Point(520, 1050);
            overlayEmptyLabel.MaximumSize = new Size(780, 0);
            overlayEmptyLabel.Name = "overlayEmptyLabel";
            overlayEmptyLabel.Size = new Size(245, 30);
            overlayEmptyLabel.TabIndex = 51;
            overlayEmptyLabel.Text = "No overlay widgets installed";
            // 
            // overlayListBox
            // 
            overlayListBox.FormattingEnabled = true;
            overlayListBox.ItemHeight = 30;
            overlayListBox.Location = new Point(520, 982);
            overlayListBox.Margin = new Padding(0, 0, 12, 0);
            overlayListBox.Name = "overlayListBox";
            overlayListBox.Size = new Size(220, 184);
            overlayListBox.TabIndex = 52;
            overlayListBox.SelectedIndexChanged += overlayListBox_SelectedIndexChanged;
            // 
            // overlayHostPanel
            // 
            overlayHostPanel.BorderStyle = BorderStyle.FixedSingle;
            overlayHostPanel.Location = new Point(750, 982);
            overlayHostPanel.Margin = new Padding(12, 0, 0, 0);
            overlayHostPanel.Name = "overlayHostPanel";
            overlayHostPanel.Size = new Size(390, 184);
            overlayHostPanel.TabIndex = 53;
            // 
            // overlayStatusLabel
            // 
            overlayStatusLabel.AutoSize = true;
            overlayStatusLabel.Location = new Point(520, 1170);
            overlayStatusLabel.Name = "overlayStatusLabel";
            overlayStatusLabel.Size = new Size(0, 30);
            overlayStatusLabel.TabIndex = 54;
            // 
            // minigamesLabel
            // 
            minigamesLabel.AutoSize = true;
            minigamesLabel.Font = new Font("Segoe UI", 10F, FontStyle.Bold, GraphicsUnit.Point);
            minigamesLabel.Margin = new Padding(0, 6, 0, 4);
            minigamesLabel.Name = "minigamesLabel";
            minigamesLabel.Size = new Size(115, 28);
            minigamesLabel.TabIndex = 55;
            minigamesLabel.Text = "Minigames";
            // 
            // minigameFiltersFlow
            // 
            minigameFiltersFlow.AutoSize = true;
            minigameFiltersFlow.AutoSizeMode = AutoSizeMode.GrowAndShrink;
            minigameFiltersFlow.FlowDirection = FlowDirection.LeftToRight;
            minigameFiltersFlow.Margin = new Padding(0, 0, 0, 4);
            minigameFiltersFlow.WrapContents = true;
            minigameFiltersFlow.Controls.Add(minigameCategoryFilterLabel);
            minigameFiltersFlow.Controls.Add(minigameCategoryFilter);
            minigameFiltersFlow.Controls.Add(minigameStatusFilterLabel);
            minigameFiltersFlow.Controls.Add(minigameStatusFilter);
            // 
            // minigameCategoryFilterLabel
            // 
            minigameCategoryFilterLabel.AutoSize = true;
            minigameCategoryFilterLabel.Margin = new Padding(0, 6, 6, 0);
            minigameCategoryFilterLabel.Name = "minigameCategoryFilterLabel";
            minigameCategoryFilterLabel.Size = new Size(88, 30);
            minigameCategoryFilterLabel.TabIndex = 0;
            minigameCategoryFilterLabel.Text = "Category";
            // 
            // minigameCategoryFilter
            // 
            minigameCategoryFilter.DropDownStyle = ComboBoxStyle.DropDownList;
            minigameCategoryFilter.Margin = new Padding(0, 0, 12, 0);
            minigameCategoryFilter.Name = "minigameCategoryFilter";
            minigameCategoryFilter.Size = new Size(180, 38);
            minigameCategoryFilter.TabIndex = 1;
            minigameCategoryFilter.SelectedIndexChanged += minigameCategoryFilter_SelectedIndexChanged;
            // 
            // minigameStatusFilterLabel
            // 
            minigameStatusFilterLabel.AutoSize = true;
            minigameStatusFilterLabel.Margin = new Padding(0, 6, 6, 0);
            minigameStatusFilterLabel.Name = "minigameStatusFilterLabel";
            minigameStatusFilterLabel.Size = new Size(68, 30);
            minigameStatusFilterLabel.TabIndex = 2;
            minigameStatusFilterLabel.Text = "Status";
            // 
            // minigameStatusFilter
            // 
            minigameStatusFilter.DropDownStyle = ComboBoxStyle.DropDownList;
            minigameStatusFilter.Margin = new Padding(0);
            minigameStatusFilter.Name = "minigameStatusFilter";
            minigameStatusFilter.Size = new Size(170, 38);
            minigameStatusFilter.TabIndex = 3;
            minigameStatusFilter.SelectedIndexChanged += minigameStatusFilter_SelectedIndexChanged;
            // 
            // minigameListView
            // 
            minigameListView.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            minigameListView.Columns.AddRange(new ColumnHeader[] { minigameNameColumn, minigameCategoryColumn, minigameStatusColumn, minigameTagsColumn, minigamePluginColumn });
            minigameListView.FullRowSelect = true;
            minigameListView.GridLines = true;
            minigameListView.Location = new Point(520, 510);
            minigameListView.Margin = new Padding(0, 4, 0, 4);
            minigameListView.MultiSelect = false;
            minigameListView.Name = "minigameListView";
            minigameListView.Size = new Size(780, 170);
            minigameListView.TabIndex = 56;
            minigameListView.UseCompatibleStateImageBehavior = false;
            minigameListView.View = View.Details;
            minigameListView.SelectedIndexChanged += minigameListView_SelectedIndexChanged;
            // 
            // minigameNameColumn
            // 
            minigameNameColumn.Text = "Name";
            minigameNameColumn.Width = 220;
            // 
            // minigameCategoryColumn
            // 
            minigameCategoryColumn.Text = "Category";
            minigameCategoryColumn.Width = 120;
            // 
            // minigameStatusColumn
            // 
            minigameStatusColumn.Text = "Status";
            minigameStatusColumn.Width = 110;
            // 
            // minigameTagsColumn
            // 
            minigameTagsColumn.Text = "Tags";
            minigameTagsColumn.Width = 160;
            // 
            // minigamePluginColumn
            // 
            minigamePluginColumn.Text = "Plugin";
            minigamePluginColumn.Width = 150;
            // 
            // minigameDetailsBox
            // 
            minigameDetailsBox.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            minigameDetailsBox.Location = new Point(520, 686);
            minigameDetailsBox.Multiline = true;
            minigameDetailsBox.Name = "minigameDetailsBox";
            minigameDetailsBox.ReadOnly = false;
            minigameDetailsBox.ScrollBars = ScrollBars.Vertical;
            minigameDetailsBox.Size = new Size(780, 120);
            minigameDetailsBox.TabIndex = 57;
            // 
            // pluginButtonsFlow
            // 
            pluginButtonsFlow.AutoSize = true;
            pluginButtonsFlow.AutoSizeMode = AutoSizeMode.GrowAndShrink;
            pluginButtonsFlow.FlowDirection = FlowDirection.LeftToRight;
            pluginButtonsFlow.Margin = new Padding(0, 6, 0, 6);
            pluginButtonsFlow.WrapContents = true;
            pluginButtonsFlow.Controls.Add(openPluginsFolderButton);
            pluginButtonsFlow.Controls.Add(reloadPluginsButton);
            pluginButtonsFlow.Controls.Add(installSamplesButton);
            pluginButtonsFlow.Controls.Add(removeSamplesButton);
            // 
            // replayButtonsFlow
            // 
            replayButtonsFlow.AutoSize = true;
            replayButtonsFlow.AutoSizeMode = AutoSizeMode.GrowAndShrink;
            replayButtonsFlow.FlowDirection = FlowDirection.LeftToRight;
            replayButtonsFlow.Margin = new Padding(0, 6, 0, 6);
            replayButtonsFlow.WrapContents = true;
            replayButtonsFlow.Controls.Add(openReplaysFolderButton);
            replayButtonsFlow.Controls.Add(refreshReplaysButton);
            // 
            // overlayLayout
            // 
            overlayLayout.AutoSize = true;
            overlayLayout.AutoSizeMode = AutoSizeMode.GrowAndShrink;
            overlayLayout.FlowDirection = FlowDirection.LeftToRight;
            overlayLayout.Margin = new Padding(0, 4, 0, 4);
            overlayLayout.WrapContents = false;
            overlayLayout.Controls.Add(overlayListBox);
            overlayLayout.Controls.Add(overlayHostPanel);
            // 
            // devLayout
            // 
            devLayout.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            devLayout.AutoScroll = true;
            devLayout.ColumnCount = 1;
            devLayout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100F));
            devLayout.Controls.Add(devOptionsLabel, 0, 0);
            devLayout.Controls.Add(policyAllowLabel, 0, 1);
            devLayout.Controls.Add(policyModeLabel, 0, 2);
            devLayout.Controls.Add(policyPathLabel, 0, 3);
            devLayout.Controls.Add(policyLoadedLabel, 0, 4);
            devLayout.Controls.Add(policyBackendLabel, 0, 5);
            devLayout.Controls.Add(policyBackendIdLabel, 0, 6);
            devLayout.Controls.Add(openPolicyFolderButton, 0, 7);
            devLayout.Controls.Add(pluginsLabel, 0, 8);
            devLayout.Controls.Add(pluginListView, 0, 9);
            devLayout.Controls.Add(pluginInstallStatusLabel, 0, 10);
            devLayout.Controls.Add(pluginButtonsFlow, 0, 11);
            devLayout.Controls.Add(minigamesLabel, 0, 12);
            devLayout.Controls.Add(minigameFiltersFlow, 0, 13);
            devLayout.Controls.Add(minigameListView, 0, 14);
            devLayout.Controls.Add(minigameDetailsBox, 0, 15);
            devLayout.Controls.Add(installFromGithubButton, 0, 16);
            devLayout.Controls.Add(replaysLabel, 0, 17);
            devLayout.Controls.Add(replayListView, 0, 18);
            devLayout.Controls.Add(replayButtonsFlow, 0, 19);
            devLayout.Controls.Add(replayDetailsBox, 0, 20);
            devLayout.Controls.Add(overlayWidgetsLabel, 0, 21);
            devLayout.Controls.Add(overlayLayout, 0, 22);
            devLayout.Controls.Add(overlayEmptyLabel, 0, 23);
            devLayout.Controls.Add(overlayStatusLabel, 0, 24);
            devLayout.Location = new Point(520, 14);
            devLayout.Name = "devLayout";
            devLayout.Padding = new Padding(6);
            devLayout.RowCount = 25;
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.RowStyles.Add(new RowStyle());
            devLayout.Size = new Size(820, 1180);
            devLayout.TabIndex = 55;
            // 
            // replaysLabel
            // 
            replaysLabel.AutoSize = true;
            replaysLabel.Font = new Font("Segoe UI", 10F, FontStyle.Bold, GraphicsUnit.Point);
            replaysLabel.Margin = new Padding(0, 6, 0, 4);
            replaysLabel.Location = new Point(520, 590);
            replaysLabel.Name = "replaysLabel";
            replaysLabel.Size = new Size(74, 28);
            replaysLabel.TabIndex = 44;
            replaysLabel.Text = "Replays";
            // 
            // replayListView
            // 
            replayListView.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            replayListView.Columns.AddRange(new ColumnHeader[] { replayNameColumn, replayDateColumn });
            replayListView.FullRowSelect = true;
            replayListView.GridLines = true;
            replayListView.Location = new Point(520, 622);
            replayListView.Margin = new Padding(0, 4, 0, 4);
            replayListView.Name = "replayListView";
            replayListView.Size = new Size(780, 140);
            replayListView.TabIndex = 45;
            replayListView.UseCompatibleStateImageBehavior = false;
            replayListView.View = View.Details;
            replayListView.MultiSelect = false;
            replayListView.SelectedIndexChanged += replayListView_SelectedIndexChanged;
            // 
            // replayNameColumn
            // 
            replayNameColumn.Text = "Replay";
            replayNameColumn.Width = 220;
            // 
            // replayDateColumn
            // 
            replayDateColumn.Text = "Modified";
            replayDateColumn.Width = 180;
            // 
            // openReplaysFolderButton
            // 
            openReplaysFolderButton.Location = new Point(520, 770);
            openReplaysFolderButton.Margin = new Padding(0, 0, 6, 0);
            openReplaysFolderButton.Name = "openReplaysFolderButton";
            openReplaysFolderButton.Size = new Size(200, 34);
            openReplaysFolderButton.TabIndex = 46;
            openReplaysFolderButton.Text = "Open Replays Folder";
            openReplaysFolderButton.UseVisualStyleBackColor = true;
            openReplaysFolderButton.Click += openReplaysFolderButton_Click;
            // 
            // refreshReplaysButton
            // 
            refreshReplaysButton.Location = new Point(730, 770);
            refreshReplaysButton.Margin = new Padding(0);
            refreshReplaysButton.Name = "refreshReplaysButton";
            refreshReplaysButton.Size = new Size(150, 34);
            refreshReplaysButton.TabIndex = 47;
            refreshReplaysButton.Text = "Refresh Replays";
            refreshReplaysButton.UseVisualStyleBackColor = true;
            refreshReplaysButton.Click += refreshReplaysButton_Click;
            // 
            // replayDetailsBox
            // 
            replayDetailsBox.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            replayDetailsBox.Location = new Point(520, 810);
            replayDetailsBox.Multiline = true;
            replayDetailsBox.Name = "replayDetailsBox";
            replayDetailsBox.ReadOnly = true;
            replayDetailsBox.ScrollBars = ScrollBars.Vertical;
            replayDetailsBox.Size = new Size(780, 120);
            replayDetailsBox.TabIndex = 48;
            // 
            // updatesLabel
            // 
            updatesLabel.AutoSize = true;
            updatesLabel.Location = new Point(14, 706);
            updatesLabel.Name = "updatesLabel";
            updatesLabel.Size = new Size(130, 30);
            updatesLabel.TabIndex = 16;
            updatesLabel.Text = "Update Feed:";
            // 
            // feedUrlText
            // 
            feedUrlText.Location = new Point(14, 740);
            feedUrlText.Name = "feedUrlText";
            feedUrlText.Size = new Size(478, 35);
            feedUrlText.TabIndex = 17;
            // 
            // autoCheckUpdatesToggle
            // 
            autoCheckUpdatesToggle.AutoSize = true;
            autoCheckUpdatesToggle.Location = new Point(14, 782);
            autoCheckUpdatesToggle.Name = "autoCheckUpdatesToggle";
            autoCheckUpdatesToggle.Size = new Size(202, 34);
            autoCheckUpdatesToggle.TabIndex = 18;
            autoCheckUpdatesToggle.Text = "Auto-check on start";
            autoCheckUpdatesToggle.UseVisualStyleBackColor = true;
            // 
            // checkUpdatesButton
            // 
            checkUpdatesButton.Location = new Point(14, 822);
            checkUpdatesButton.Name = "checkUpdatesButton";
            checkUpdatesButton.Size = new Size(150, 34);
            checkUpdatesButton.TabIndex = 19;
            checkUpdatesButton.Text = "Check";
            checkUpdatesButton.UseVisualStyleBackColor = true;
            checkUpdatesButton.Click += checkUpdatesButton_Click;
            // 
            // downloadUpdateButton
            // 
            downloadUpdateButton.Location = new Point(170, 822);
            downloadUpdateButton.Name = "downloadUpdateButton";
            downloadUpdateButton.Size = new Size(150, 34);
            downloadUpdateButton.TabIndex = 20;
            downloadUpdateButton.Text = "Download";
            downloadUpdateButton.UseVisualStyleBackColor = true;
            downloadUpdateButton.Click += downloadUpdateButton_Click;
            // 
            // applyUpdateButton
            // 
            applyUpdateButton.Location = new Point(326, 822);
            applyUpdateButton.Name = "applyUpdateButton";
            applyUpdateButton.Size = new Size(150, 34);
            applyUpdateButton.TabIndex = 21;
            applyUpdateButton.Text = "Stage/Apply";
            applyUpdateButton.UseVisualStyleBackColor = true;
            applyUpdateButton.Click += applyUpdateButton_Click;
            // 
            // updaterStatusLabel
            // 
            updaterStatusLabel.AutoSize = true;
            updaterStatusLabel.Location = new Point(14, 866);
            updaterStatusLabel.Name = "updaterStatusLabel";
            updaterStatusLabel.Size = new Size(122, 30);
            updaterStatusLabel.TabIndex = 22;
            updaterStatusLabel.Text = "Status: Idle";
            // 
            // launchManagerButton
            // 
            launchManagerButton.Location = new Point(14, 901);
            launchManagerButton.Name = "launchManagerButton";
            launchManagerButton.Size = new Size(478, 34);
            launchManagerButton.TabIndex = 23;
            launchManagerButton.Text = "Open Project Manager";
            launchManagerButton.UseVisualStyleBackColor = true;
            launchManagerButton.Click += launchManagerButton_Click;
            // 
            // openMapViewerButton
            // 
            openMapViewerButton.Location = new Point(14, 941);
            openMapViewerButton.Name = "openMapViewerButton";
            openMapViewerButton.Size = new Size(478, 34);
            openMapViewerButton.TabIndex = 24;
            openMapViewerButton.Text = "Open Map Viewer";
            openMapViewerButton.UseVisualStyleBackColor = true;
            openMapViewerButton.Click += openMapViewerButton_Click;
            // 
            // refreshWikiButton
            // 
            refreshWikiButton.Location = new Point(14, 981);
            refreshWikiButton.Name = "refreshWikiButton";
            refreshWikiButton.Size = new Size(478, 34);
            refreshWikiButton.TabIndex = 25;
            refreshWikiButton.Text = "Refresh Wiki Cache";
            refreshWikiButton.UseVisualStyleBackColor = true;
            refreshWikiButton.Click += refreshWikiButton_Click;
            // 
            // runDiagnosticsButton
            // 
            runDiagnosticsButton.Location = new Point(14, 1021);
            runDiagnosticsButton.Name = "runDiagnosticsButton";
            runDiagnosticsButton.Size = new Size(478, 34);
            runDiagnosticsButton.TabIndex = 26;
            runDiagnosticsButton.Text = "Run Diagnostics (Dev)";
            runDiagnosticsButton.UseVisualStyleBackColor = true;
            runDiagnosticsButton.Visible = false;
            runDiagnosticsButton.Click += runDiagnosticsButton_Click;
            // 
            // viewDevSuggestionsButton
            // 
            viewDevSuggestionsButton.Location = new Point(14, 1061);
            viewDevSuggestionsButton.Name = "viewDevSuggestionsButton";
            viewDevSuggestionsButton.Size = new Size(478, 34);
            viewDevSuggestionsButton.TabIndex = 27;
            viewDevSuggestionsButton.Text = "View Dev Suggestions";
            viewDevSuggestionsButton.UseVisualStyleBackColor = true;
            viewDevSuggestionsButton.Visible = false;
            viewDevSuggestionsButton.Click += viewDevSuggestionsButton_Click;
            // 
            // SettingsForm
            // 
            AutoScaleDimensions = new SizeF(12F, 30F);
            AutoScaleMode = AutoScaleMode.Font;
            ClientSize = new Size(1500, 1250);
            Controls.Add(goldCapNumeric);
            Controls.Add(goldCapLabel);
            Controls.Add(goldMinNumeric);
            Controls.Add(goldMinLabel);
            Controls.Add(autoPauseToggle);
            Controls.Add(openMapViewerButton);
            Controls.Add(refreshWikiButton);
            Controls.Add(viewDevSuggestionsButton);
            Controls.Add(runDiagnosticsButton);
            Controls.Add(launchManagerButton);
            Controls.Add(captureUiSnapshotButton);
            Controls.Add(devUiSnapshotsToggle);
            Controls.Add(playerPreviewToggle);
            Controls.Add(devTelemetryToggle);
            Controls.Add(audioDeltaNumeric);
            Controls.Add(audioDeltaLabel);
            Controls.Add(tuningToggle);
            Controls.Add(audioToggle);
            Controls.Add(captureToggle);
            Controls.Add(updaterStatusLabel);
            Controls.Add(applyUpdateButton);
            Controls.Add(downloadUpdateButton);
            Controls.Add(checkUpdatesButton);
            Controls.Add(autoCheckUpdatesToggle);
            Controls.Add(feedUrlText);
            Controls.Add(updatesLabel);
            Controls.Add(themeModeCombo);
            Controls.Add(themeModeLabel);
            Controls.Add(selectedGameResolution);
            Controls.Add(label2);
            Controls.Add(saveSettingsBtn);
            Controls.Add(ocrSpaceApiKey);
            Controls.Add(label1);
            Controls.Add(devLayout);
            Name = "SettingsForm";
            Text = "Settings";
            Load += SettingsForm_Load;
            ((System.ComponentModel.ISupportInitialize)audioDeltaNumeric).EndInit();
            ((System.ComponentModel.ISupportInitialize)goldMinNumeric).EndInit();
            ((System.ComponentModel.ISupportInitialize)goldCapNumeric).EndInit();
            ResumeLayout(false);
            PerformLayout();
        }

        #endregion

        private Label label1;
        private TextBox ocrSpaceApiKey;
        private Button saveSettingsBtn;
        private Label label2;
        private ComboBox selectedGameResolution;
        private Label themeModeLabel;
        private ComboBox themeModeCombo;
        private CheckBox captureToggle;
        private CheckBox audioToggle;
        private CheckBox tuningToggle;
        private CheckBox devTelemetryToggle;
        private CheckBox devUiSnapshotsToggle;
        private Button captureUiSnapshotButton;
        private CheckBox playerPreviewToggle;
        private CheckBox autoPauseToggle;
        private Label audioDeltaLabel;
        private NumericUpDown audioDeltaNumeric;
        private Label updatesLabel;
        private TextBox feedUrlText;
        private CheckBox autoCheckUpdatesToggle;
        private Button checkUpdatesButton;
        private Button downloadUpdateButton;
        private Button applyUpdateButton;
        private Label updaterStatusLabel;
        private Button launchManagerButton;
        private Button openMapViewerButton;
        private Button refreshWikiButton = null!;
        private Button runDiagnosticsButton;
        private Button viewDevSuggestionsButton;
        private Label goldMinLabel;
        private NumericUpDown goldMinNumeric;
        private Label goldCapLabel;
        private NumericUpDown goldCapNumeric;
        private Label devOptionsLabel;
        private Label policyAllowLabel;
        private Label policyModeLabel;
        private Label policyPathLabel;
        private Label policyLoadedLabel;
        private Button openPolicyFolderButton;
        private Label policyBackendLabel;
        private Label policyBackendIdLabel;
        private Label pluginsLabel;
        private ListView pluginListView;
        private ColumnHeader pluginColumn;
        private ColumnHeader versionColumn;
        private ColumnHeader capabilitiesColumn;
        private ColumnHeader statusColumn;
        private ColumnHeader reasonColumn;
        private Button openPluginsFolderButton;
        private Button reloadPluginsButton;
        private Button installSamplesButton;
        private Button removeSamplesButton;
        private Button installFromGithubButton;
        private Label pluginInstallStatusLabel;
        private Label replaysLabel;
        private ListView replayListView;
        private ColumnHeader replayNameColumn;
        private ColumnHeader replayDateColumn;
        private Button openReplaysFolderButton;
        private Button refreshReplaysButton;
        private TextBox replayDetailsBox;
        private Label overlayWidgetsLabel;
        private FlowLayoutPanel overlayFlowPanel;
        private Label overlayEmptyLabel;
        private ListBox overlayListBox;
        private Panel overlayHostPanel;
        private Label overlayStatusLabel;
        private Label minigamesLabel;
        private FlowLayoutPanel minigameFiltersFlow;
        private Label minigameCategoryFilterLabel;
        private ComboBox minigameCategoryFilter;
        private Label minigameStatusFilterLabel;
        private ComboBox minigameStatusFilter;
        private ListView minigameListView;
        private ColumnHeader minigameNameColumn;
        private ColumnHeader minigameCategoryColumn;
        private ColumnHeader minigameStatusColumn;
        private ColumnHeader minigameTagsColumn;
        private ColumnHeader minigamePluginColumn;
        private TextBox minigameDetailsBox;
        private FlowLayoutPanel pluginButtonsFlow;
        private FlowLayoutPanel replayButtonsFlow;
        private FlowLayoutPanel overlayLayout;
        private TableLayoutPanel devLayout;
    }
}
