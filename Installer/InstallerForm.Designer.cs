namespace Installer
{
    partial class InstallerForm
    {
        /// <summary>
        ///  Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        ///  Clean up any resources being used.
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
        ///  Required method for Designer support - do not modify
        ///  the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            titleLabel = new Label();
            feedLabel = new Label();
            feedText = new TextBox();
            checkButton = new Button();
            installButton = new Button();
            uninstallButton = new Button();
            createPortableButton = new Button();
            updateButton = new Button();
            statusLabel = new Label();
            installedVersionLabel = new Label();
            latestVersionLabel = new Label();
            progressBar = new ProgressBar();
            stepLabel = new Label();
            activityList = new ListBox();
            devButton = new Button();
            installPathLabel = new Label();
            installPathText = new TextBox();
            browseInstallButton = new Button();
            desktopShortcutCheck = new CheckBox();
            startMenuShortcutCheck = new CheckBox();
            uninstallShortcutCheck = new CheckBox();
            autoCheckUpdatesCheck = new CheckBox();
            cleanInstallCheck = new CheckBox();
            launchAfterInstallCheck = new CheckBox();
            openReleaseNotesCheck = new CheckBox();
            scriptsLabel = new Label();
            scriptsList = new CheckedListBox();
            openLogButton = new Button();
            logPathLabel = new Label();
            openInstallFolderButton = new Button();
            openLibraryButton = new Button();
            launchAppButton = new Button();
            smartPlayInitCheck = new CheckBox();
            manualSourceButton = new Button();
            SuspendLayout();
            // 
            // titleLabel
            // 
            titleLabel.AutoSize = true;
            titleLabel.Font = new Font("Segoe UI", 12F, FontStyle.Bold, GraphicsUnit.Point);
            titleLabel.Location = new Point(12, 9);
            titleLabel.Name = "titleLabel";
            titleLabel.Size = new Size(295, 28);
            titleLabel.TabIndex = 0;
            titleLabel.Text = "Project Maelstrom Project Manager";
            // 
            // feedLabel
            // 
            feedLabel.AutoSize = true;
            feedLabel.Location = new Point(12, 50);
            feedLabel.Name = "feedLabel";
            feedLabel.Size = new Size(187, 20);
            feedLabel.TabIndex = 1;
            feedLabel.Text = "Update feed (optional):";
            // 
            // feedText
            // 
            feedText.Location = new Point(12, 74);
            feedText.Name = "feedText";
            feedText.Size = new Size(500, 27);
            feedText.TabIndex = 2;
            // 
            // checkButton
            // 
            checkButton.Location = new Point(518, 74);
            checkButton.Name = "checkButton";
            checkButton.Size = new Size(94, 29);
            checkButton.TabIndex = 3;
            checkButton.Text = "Check";
            checkButton.UseVisualStyleBackColor = true;
            checkButton.Click += checkButton_Click;
            // 
            // installPathLabel
            // 
            installPathLabel.AutoSize = true;
            installPathLabel.Location = new Point(12, 110);
            installPathLabel.Name = "installPathLabel";
            installPathLabel.Size = new Size(144, 20);
            installPathLabel.TabIndex = 13;
            installPathLabel.Text = "Install location:";
            // 
            // installPathText
            // 
            installPathText.Location = new Point(12, 134);
            installPathText.Name = "installPathText";
            installPathText.Size = new Size(500, 27);
            installPathText.TabIndex = 14;
            // 
            // browseInstallButton
            // 
            browseInstallButton.Location = new Point(518, 134);
            browseInstallButton.Name = "browseInstallButton";
            browseInstallButton.Size = new Size(94, 29);
            browseInstallButton.TabIndex = 15;
            browseInstallButton.Text = "Browse";
            browseInstallButton.UseVisualStyleBackColor = true;
            browseInstallButton.Click += browseInstallButton_Click;
            // 
            // desktopShortcutCheck
            // 
            desktopShortcutCheck.AutoSize = true;
            desktopShortcutCheck.Checked = true;
            desktopShortcutCheck.CheckState = CheckState.Checked;
            desktopShortcutCheck.Location = new Point(12, 172);
            desktopShortcutCheck.Name = "desktopShortcutCheck";
            desktopShortcutCheck.Size = new Size(159, 24);
            desktopShortcutCheck.TabIndex = 16;
            desktopShortcutCheck.Text = "Desktop shortcut";
            desktopShortcutCheck.UseVisualStyleBackColor = true;
            // 
            // startMenuShortcutCheck
            // 
            startMenuShortcutCheck.AutoSize = true;
            startMenuShortcutCheck.Checked = true;
            startMenuShortcutCheck.CheckState = CheckState.Checked;
            startMenuShortcutCheck.Location = new Point(177, 172);
            startMenuShortcutCheck.Name = "startMenuShortcutCheck";
            startMenuShortcutCheck.Size = new Size(178, 24);
            startMenuShortcutCheck.TabIndex = 17;
            startMenuShortcutCheck.Text = "Start menu shortcut";
            startMenuShortcutCheck.UseVisualStyleBackColor = true;
            // 
            // uninstallShortcutCheck
            // 
            uninstallShortcutCheck.AutoSize = true;
            uninstallShortcutCheck.Checked = true;
            uninstallShortcutCheck.CheckState = CheckState.Checked;
            uninstallShortcutCheck.Location = new Point(361, 172);
            uninstallShortcutCheck.Name = "uninstallShortcutCheck";
            uninstallShortcutCheck.Size = new Size(146, 24);
            uninstallShortcutCheck.TabIndex = 18;
            uninstallShortcutCheck.Text = "Uninstall shortcut";
            uninstallShortcutCheck.UseVisualStyleBackColor = true;
            // 
            // autoCheckUpdatesCheck
            // 
            autoCheckUpdatesCheck.AutoSize = true;
            autoCheckUpdatesCheck.Checked = true;
            autoCheckUpdatesCheck.CheckState = CheckState.Checked;
            autoCheckUpdatesCheck.Location = new Point(12, 202);
            autoCheckUpdatesCheck.Name = "autoCheckUpdatesCheck";
            autoCheckUpdatesCheck.Size = new Size(194, 24);
            autoCheckUpdatesCheck.TabIndex = 19;
            autoCheckUpdatesCheck.Text = "Auto-check updates on start";
            autoCheckUpdatesCheck.UseVisualStyleBackColor = true;
            autoCheckUpdatesCheck.CheckedChanged += autoCheckUpdatesCheck_CheckedChanged;
            // 
            // cleanInstallCheck
            // 
            cleanInstallCheck.AutoSize = true;
            cleanInstallCheck.Checked = true;
            cleanInstallCheck.CheckState = CheckState.Checked;
            cleanInstallCheck.Location = new Point(212, 202);
            cleanInstallCheck.Name = "cleanInstallCheck";
            cleanInstallCheck.Size = new Size(105, 24);
            cleanInstallCheck.TabIndex = 20;
            cleanInstallCheck.Text = "Clean install";
            cleanInstallCheck.UseVisualStyleBackColor = true;
            // 
            // launchAfterInstallCheck
            // 
            launchAfterInstallCheck.AutoSize = true;
            launchAfterInstallCheck.Location = new Point(323, 202);
            launchAfterInstallCheck.Name = "launchAfterInstallCheck";
            launchAfterInstallCheck.Size = new Size(147, 24);
            launchAfterInstallCheck.TabIndex = 21;
            launchAfterInstallCheck.Text = "Launch after install";
            launchAfterInstallCheck.UseVisualStyleBackColor = true;
            // 
            // openReleaseNotesCheck
            // 
            openReleaseNotesCheck.AutoSize = true;
            openReleaseNotesCheck.Location = new Point(476, 202);
            openReleaseNotesCheck.Name = "openReleaseNotesCheck";
            openReleaseNotesCheck.Size = new Size(156, 24);
            openReleaseNotesCheck.TabIndex = 22;
            openReleaseNotesCheck.Text = "Open release notes";
            openReleaseNotesCheck.UseVisualStyleBackColor = true;
            // installButton
            // 
            installButton.Location = new Point(12, 232);
            installButton.Name = "installButton";
            installButton.Size = new Size(150, 34);
            installButton.TabIndex = 4;
            installButton.Text = "Fresh Install";
            installButton.UseVisualStyleBackColor = true;
            installButton.Click += installButton_Click;
            // 
            // uninstallButton
            // 
            uninstallButton.Location = new Point(168, 232);
            uninstallButton.Name = "uninstallButton";
            uninstallButton.Size = new Size(150, 34);
            uninstallButton.TabIndex = 5;
            uninstallButton.Text = "Uninstall";
            uninstallButton.UseVisualStyleBackColor = true;
            uninstallButton.Click += uninstallButton_Click;
            // 
            // createPortableButton
            // 
            createPortableButton.Location = new Point(324, 232);
            createPortableButton.Name = "createPortableButton";
            createPortableButton.Size = new Size(150, 34);
            createPortableButton.TabIndex = 6;
            createPortableButton.Text = "Create Portable";
            createPortableButton.UseVisualStyleBackColor = true;
            createPortableButton.Click += createPortableButton_Click;
            // 
            // updateButton
            // 
            updateButton.Location = new Point(480, 232);
            updateButton.Name = "updateButton";
            updateButton.Size = new Size(132, 34);
            updateButton.TabIndex = 7;
            updateButton.Text = "Update";
            updateButton.UseVisualStyleBackColor = true;
            updateButton.Click += updateButton_Click;
            // 
            // launchAppButton
            // 
            launchAppButton.Location = new Point(480, 270);
            launchAppButton.Name = "launchAppButton";
            launchAppButton.Size = new Size(318, 34);
            launchAppButton.TabIndex = 34;
            launchAppButton.Text = "Launch Project Maelstrom";
            launchAppButton.UseVisualStyleBackColor = true;
            launchAppButton.Click += launchAppButton_Click;
            // 
            // statusLabel
            // 
            statusLabel.AutoSize = true;
            statusLabel.Location = new Point(12, 260);
            statusLabel.Name = "statusLabel";
            statusLabel.Size = new Size(114, 20);
            statusLabel.TabIndex = 6;
            statusLabel.Text = "Status: Waiting";
            // 
            // installedVersionLabel
            // 
            installedVersionLabel.AutoSize = true;
            installedVersionLabel.Location = new Point(12, 214);
            installedVersionLabel.Name = "installedVersionLabel";
            installedVersionLabel.Size = new Size(138, 20);
            installedVersionLabel.TabIndex = 7;
            installedVersionLabel.Text = "Installed: Unknown";
            // 
            // latestVersionLabel
            // 
            latestVersionLabel.AutoSize = true;
            latestVersionLabel.Location = new Point(250, 214);
            latestVersionLabel.Name = "latestVersionLabel";
            latestVersionLabel.Size = new Size(121, 20);
            latestVersionLabel.TabIndex = 8;
            latestVersionLabel.Text = "Latest: Unknown";
            // 
            // progressBar
            // 
            progressBar.Location = new Point(12, 570);
            progressBar.Name = "progressBar";
            progressBar.Size = new Size(600, 20);
            progressBar.Style = ProgressBarStyle.Continuous;
            progressBar.TabIndex = 9;
            // 
            // stepLabel
            // 
            stepLabel.AutoSize = true;
            stepLabel.Location = new Point(12, 600);
            stepLabel.Name = "stepLabel";
            stepLabel.Size = new Size(145, 20);
            stepLabel.TabIndex = 10;
            stepLabel.Text = "Step: Ready to start";
            // 
            // activityList
            // 
            activityList.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
            activityList.FormattingEnabled = true;
            activityList.ItemHeight = 20;
            activityList.Location = new Point(12, 330);
            activityList.Name = "activityList";
            activityList.Size = new Size(300, 224);
            activityList.TabIndex = 11;
            // 
            // devButton
            // 
            devButton.Anchor = AnchorStyles.Top | AnchorStyles.Right;
            devButton.Location = new Point(518, 12);
            devButton.Name = "devButton";
            devButton.Size = new Size(94, 29);
            devButton.TabIndex = 12;
            devButton.Text = "Dev";
            devButton.UseVisualStyleBackColor = true;
            devButton.Visible = false;
            devButton.Click += devButton_Click;
            // 
            // scriptsLabel
            // 
            scriptsLabel.AutoSize = true;
            scriptsLabel.Location = new Point(330, 330);
            scriptsLabel.Name = "scriptsLabel";
            scriptsLabel.Size = new Size(142, 20);
            scriptsLabel.TabIndex = 23;
            scriptsLabel.Text = "Scripts / Add-ons:";
            // 
            // scriptsList
            // 
            scriptsList.CheckOnClick = true;
            scriptsList.FormattingEnabled = true;
            scriptsList.Location = new Point(330, 353);
            scriptsList.Name = "scriptsList";
            scriptsList.Size = new Size(282, 180);
            scriptsList.TabIndex = 24;
            // 
            // openLogButton
            // 
            openLogButton.Location = new Point(12, 300);
            openLogButton.Name = "openLogButton";
            openLogButton.Size = new Size(140, 27);
            openLogButton.TabIndex = 25;
            openLogButton.Text = "Open Log Folder";
            openLogButton.UseVisualStyleBackColor = true;
            openLogButton.Click += openLogButton_Click;
            // 
            // logPathLabel
            // 
            logPathLabel.AutoSize = true;
            logPathLabel.Location = new Point(160, 304);
            logPathLabel.Name = "logPathLabel";
            logPathLabel.Size = new Size(0, 20);
            logPathLabel.TabIndex = 26;
            // 
            // openInstallFolderButton
            // 
            openInstallFolderButton.Location = new Point(12, 626);
            openInstallFolderButton.Name = "openInstallFolderButton";
            openInstallFolderButton.Size = new Size(140, 27);
            openInstallFolderButton.TabIndex = 27;
            openInstallFolderButton.Text = "Open Install Folder";
            openInstallFolderButton.UseVisualStyleBackColor = true;
            openInstallFolderButton.Click += openInstallFolderButton_Click;
            // 
            // openLibraryButton
            // 
            openLibraryButton.Location = new Point(158, 626);
            openLibraryButton.Name = "openLibraryButton";
            openLibraryButton.Size = new Size(140, 27);
            openLibraryButton.TabIndex = 28;
            openLibraryButton.Text = "Open Script Library";
            openLibraryButton.UseVisualStyleBackColor = true;
            openLibraryButton.Click += openLibraryButton_Click;
            // 
            // launchAppButton
            // 
            launchAppButton.Location = new Point(304, 626);
            launchAppButton.Name = "launchAppButton";
            launchAppButton.Size = new Size(140, 27);
            launchAppButton.TabIndex = 29;
            launchAppButton.Text = "Launch App";
            launchAppButton.UseVisualStyleBackColor = true;
            launchAppButton.Click += launchAppButton_Click;
            // 
            // smartPlayInitCheck
            // 
            smartPlayInitCheck.AutoSize = true;
            smartPlayInitCheck.Checked = true;
            smartPlayInitCheck.CheckState = CheckState.Checked;
            smartPlayInitCheck.Location = new Point(438, 304);
            smartPlayInitCheck.Name = "smartPlayInitCheck";
            smartPlayInitCheck.Size = new Size(174, 24);
            smartPlayInitCheck.TabIndex = 30;
            smartPlayInitCheck.Text = "Init SmartPlay cache";
            smartPlayInitCheck.UseVisualStyleBackColor = true;
            // 
            // manualSourceButton
            // 
            manualSourceButton.Location = new Point(12, 270);
            manualSourceButton.Name = "manualSourceButton";
            manualSourceButton.Size = new Size(188, 27);
            manualSourceButton.TabIndex = 31;
            manualSourceButton.Text = "Manual source/package...";
            manualSourceButton.UseVisualStyleBackColor = true;
            manualSourceButton.Visible = false;
            manualSourceButton.Click += manualSourceButton_Click;
            // 
            // InstallerForm
            // 
            AutoScaleDimensions = new SizeF(8F, 20F);
            AutoScaleMode = AutoScaleMode.Font;
            ClientSize = new Size(640, 640);
            Controls.Add(manualSourceButton);
            Controls.Add(smartPlayInitCheck);
            Controls.Add(launchAppButton);
            Controls.Add(openLibraryButton);
            Controls.Add(openInstallFolderButton);
            Controls.Add(logPathLabel);
            Controls.Add(openLogButton);
            Controls.Add(scriptsList);
            Controls.Add(scriptsLabel);
            Controls.Add(openReleaseNotesCheck);
            Controls.Add(launchAfterInstallCheck);
            Controls.Add(cleanInstallCheck);
            Controls.Add(autoCheckUpdatesCheck);
            Controls.Add(uninstallShortcutCheck);
            Controls.Add(startMenuShortcutCheck);
            Controls.Add(desktopShortcutCheck);
            Controls.Add(browseInstallButton);
            Controls.Add(installPathText);
            Controls.Add(installPathLabel);
            Controls.Add(devButton);
            Controls.Add(progressBar);
            Controls.Add(activityList);
            Controls.Add(stepLabel);
            Controls.Add(latestVersionLabel);
            Controls.Add(installedVersionLabel);
            Controls.Add(statusLabel);
            Controls.Add(updateButton);
            Controls.Add(createPortableButton);
            Controls.Add(uninstallButton);
            Controls.Add(installButton);
            Controls.Add(checkButton);
            Controls.Add(feedText);
            Controls.Add(feedLabel);
            Controls.Add(titleLabel);
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false;
            MinimizeBox = false;
            Name = "InstallerForm";
            StartPosition = FormStartPosition.CenterScreen;
            Text = "Project Maelstrom Installer";
            Load += InstallerForm_Load;
            ResumeLayout(false);
            PerformLayout();
        }

        #endregion

        private Label titleLabel;
        private Label feedLabel;
        private TextBox feedText;
        private Button checkButton;
        private Button installButton;
        private Button uninstallButton;
        private Button createPortableButton;
        private Button updateButton;
        private Button launchAppButton;
        private Label statusLabel;
        private Label installedVersionLabel;
        private Label latestVersionLabel;
        private ProgressBar progressBar;
        private Label stepLabel;
        private ListBox activityList;
        private Button devButton;
        private Label installPathLabel;
        private TextBox installPathText;
        private Button browseInstallButton;
        private CheckBox desktopShortcutCheck;
        private CheckBox startMenuShortcutCheck;
        private CheckBox uninstallShortcutCheck;
        private CheckBox autoCheckUpdatesCheck;
        private CheckBox cleanInstallCheck;
        private CheckBox launchAfterInstallCheck;
        private CheckBox openReleaseNotesCheck;
        private Label scriptsLabel;
        private CheckedListBox scriptsList;
        private Button openLogButton;
        private Label logPathLabel;
        private Button openInstallFolderButton;
        private Button openLibraryButton;
        private CheckBox smartPlayInitCheck;
        private Button manualSourceButton;
    }
}
