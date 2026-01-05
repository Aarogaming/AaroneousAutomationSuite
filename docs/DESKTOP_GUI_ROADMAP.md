# AAS Desktop GUI Roadmap

> **Part of**: [MASTER_ROADMAP.md](MASTER_ROADMAP.md) § Phase 2.2 - Native Desktop GUI

**Status**: 60-70% Complete  
**Target Completion**: Q1 2026  
**Owner**: AAS Core Team

## Executive Summary

Transform the existing web-based Mission Control dashboard into a fully native desktop application with offline capabilities, system integration, and professional distribution. Leverage existing React dashboard (~900 lines) and system tray app to accelerate development.

## Current State Assessment

### ✅ Implemented Components

1. **Web Dashboard** (`dashboard/`)
   - React 19 + TypeScript + Vite
   - Real-time task monitoring via Socket.IO
   - Agent status tracking
   - Ollama model management
   - Activity logs and health metrics
   - Tailwind CSS styling
   - **Lines of Code**: ~905 (App.tsx)

2. **System Tray Integration** (`scripts/aas_tray.py`)
   - Python `pystray` application
   - Start/Stop/Restart Hub controls
   - Status monitoring with PID tracking
   - Quick dashboard launcher
   - Log file viewer integration
   - Dynamic menu updates every 5s

3. **Backend Services**
   - Flask web server (`core/web/app.py`)
   - WebSocket event streaming
   - REST API endpoints
   - gRPC server for IPC

### ❌ Missing Components

- Desktop application wrapper (Electron/Tauri)
- Offline mode capabilities
- Native window management
- System notifications (native)
- File system dialogs
- Auto-updater mechanism
- Professional installers (MSI/EXE)
- Cross-platform builds
- Application signing

---

## Implementation Plan

### Phase 1: Desktop Packaging Foundation (Week 1)
**Goal**: Wrap existing React dashboard in native desktop framework

#### Task 1.1: Technology Selection ✓ Decision Made
**Duration**: 1 day  
**Assignee**: Lead Developer

**Options Analysis**:
- ✅ **Tauri (Recommended)**
  - Pros: Rust-based, 600KB bundles, better security, native performance
  - Cons: Smaller community, newer ecosystem
  - Best for: Performance-critical, security-focused desktop apps
  
- **Electron**
  - Pros: Mature ecosystem, extensive plugins, VS Code uses it
  - Cons: 50MB+ bundles, higher memory usage
  - Best for: Rapid development, extensive native API needs

**Decision**: Tauri for production builds, keeping web dashboard for development.

**Deliverables**:
- [ ] Technology decision document
- [ ] Proof-of-concept build

#### Task 1.2: Project Structure Setup
**Duration**: 1 day  
**Dependencies**: Task 1.1

**Steps**:
1. Install Tauri CLI
   ```bash
   cargo install tauri-cli
   npm install --save-dev @tauri-apps/cli
   ```

2. Initialize Tauri in dashboard directory
   ```bash
   cd dashboard
   npm install @tauri-apps/api
   npx tauri init
   ```

3. Configure `tauri.conf.json`:
   - App name: "AAS Mission Control"
   - Window size: 1400x900
   - Dev server: http://localhost:5174
   - Icon paths (Windows, Linux, macOS)

4. Update `package.json` scripts:
   ```json
   {
     "tauri:dev": "tauri dev",
     "tauri:build": "tauri build"
   }
   ```

**Deliverables**:
- [ ] `src-tauri/` directory with Rust backend
- [ ] `tauri.conf.json` configured
- [ ] Updated build scripts

#### Task 1.3: Native Window Integration
**Duration**: 2 days  
**Dependencies**: Task 1.2

**Implementation**:

1. **Custom Title Bar** (optional, for modern look)
   ```typescript
   // src/components/TitleBar.tsx
   import { appWindow } from '@tauri-apps/api/window';
   
   export function TitleBar() {
     return (
       <div data-tauri-drag-region className="titlebar">
         <span>AAS Mission Control</span>
         <div className="controls">
           <button onClick={() => appWindow.minimize()}>−</button>
           <button onClick={() => appWindow.toggleMaximize()}>□</button>
           <button onClick={() => appWindow.close()}>×</button>
         </div>
       </div>
     );
   }
   ```

2. **Window State Management**
   ```typescript
   // src/hooks/useWindowState.ts
   import { appWindow } from '@tauri-apps/api/window';
   
   export function useWindowState() {
     const minimize = () => appWindow.hide();
     const restore = () => appWindow.show();
     const closeToTray = () => appWindow.hide(); // Don't quit
     
     return { minimize, restore, closeToTray };
   }
   ```

3. **System Tray Integration** (Rust side)
   ```rust
   // src-tauri/src/main.rs
   use tauri::{SystemTray, SystemTrayMenu, SystemTrayEvent};
   
   fn create_tray_menu() -> SystemTray {
       let menu = SystemTrayMenu::new()
           .add_item(CustomMenuItem::new("show", "Show Mission Control"))
           .add_item(CustomMenuItem::new("hide", "Hide"))
           .add_native_item(SystemTrayMenuItem::Separator)
           .add_item(CustomMenuItem::new("start_hub", "Start Hub"))
           .add_item(CustomMenuItem::new("stop_hub", "Stop Hub"))
           .add_item(CustomMenuItem::new("restart_hub", "Restart Hub"))
           .add_native_item(SystemTrayMenuItem::Separator)
           .add_item(CustomMenuItem::new("quit", "Quit"));
       
       SystemTray::new().with_menu(menu)
   }
   ```

**Deliverables**:
- [ ] Custom window controls
- [ ] System tray menu
- [ ] Window state persistence
- [ ] Close-to-tray behavior

#### Task 1.4: Native API Integration
**Duration**: 2 days  
**Dependencies**: Task 1.3

**Features**:

1. **File System Access**
   ```typescript
   // src/services/native.ts
   import { open, save } from '@tauri-apps/api/dialog';
   import { writeTextFile, readTextFile } from '@tauri-apps/api/fs';
   
   export async function exportLogs() {
     const path = await save({
       filters: [{ name: 'Log File', extensions: ['log'] }]
     });
     if (path) {
       await writeTextFile(path, logsContent);
     }
   }
   ```

2. **Native Notifications**
   ```typescript
   import { sendNotification } from '@tauri-apps/api/notification';
   
   export function notifyTaskComplete(taskId: string) {
     sendNotification({
       title: 'AAS Hub',
       body: `Task ${taskId} completed successfully`
     });
   }
   ```

3. **Shell Commands** (controlled via Rust for security)
   ```rust
   // src-tauri/src/commands.rs
   #[tauri::command]
   async fn start_hub() -> Result<String, String> {
       // Execute start_hub.ps1 safely
       Ok("Hub started".to_string())
   }
   
   #[tauri::command]
   async fn get_hub_status() -> Result<String, String> {
       // Check PID file
       Ok("Running".to_string())
   }
   ```

**Deliverables**:
- [ ] File dialog integration
- [ ] Native notifications
- [ ] Secure command execution
- [ ] System integration tests

---

### Phase 2: Python Tray App Migration (Week 2)
**Goal**: Consolidate Python tray functionality into native app

#### Task 2.1: Feature Parity Analysis
**Duration**: 0.5 days

**Existing `aas_tray.py` Features**:
- ✓ Check if Hub is running (PID file)
- ✓ Start Hub (PowerShell script)
- ✓ Stop Hub (PowerShell script)
- ✓ Restart Hub (PowerShell script)
- ✓ Show status (notify)
- ✓ Open dashboard (browser)
- ✓ Open logs (Notepad)
- ✓ Dynamic menu updates

**Migration Strategy**: Move all logic to Tauri Rust backend + React frontend.

#### Task 2.2: Hub Control Commands
**Duration**: 1 day  
**Dependencies**: Task 2.1

**Implementation**:

```rust
// src-tauri/src/hub_manager.rs
use std::process::Command;
use std::fs;
use std::path::PathBuf;

pub struct HubManager {
    root_dir: PathBuf,
    pid_file: PathBuf,
}

impl HubManager {
    pub fn new() -> Self {
        let root = std::env::current_dir().unwrap();
        HubManager {
            pid_file: root.join("artifacts/hub.pid"),
            root_dir: root,
        }
    }
    
    pub fn is_running(&self) -> bool {
        if !self.pid_file.exists() {
            return false;
        }
        
        let pid = fs::read_to_string(&self.pid_file)
            .unwrap_or_default()
            .trim()
            .to_string();
        
        // Check if process exists (Windows)
        Command::new("powershell")
            .args(&["-Command", &format!("Get-Process -Id {} -ErrorAction SilentlyContinue", pid)])
            .output()
            .map(|o| o.status.success())
            .unwrap_or(false)
    }
    
    pub fn start(&self) -> Result<String, String> {
        let script = self.root_dir.join("scripts/start_hub.ps1");
        Command::new("powershell")
            .args(&["-ExecutionPolicy", "Bypass", "-File", script.to_str().unwrap()])
            .current_dir(&self.root_dir)
            .spawn()
            .map(|_| "Hub started".to_string())
            .map_err(|e| e.to_string())
    }
    
    pub fn stop(&self) -> Result<String, String> {
        let script = self.root_dir.join("scripts/start_hub.ps1");
        Command::new("powershell")
            .args(&["-ExecutionPolicy", "Bypass", "-File", script.to_str().unwrap(), "-Stop"])
            .current_dir(&self.root_dir)
            .spawn()
            .map(|_| "Hub stopped".to_string())
            .map_err(|e| e.to_string())
    }
    
    pub fn restart(&self) -> Result<String, String> {
        let script = self.root_dir.join("scripts/start_hub.ps1");
        Command::new("powershell")
            .args(&["-ExecutionPolicy", "Bypass", "-File", script.to_str().unwrap(), "-Restart"])
            .current_dir(&self.root_dir)
            .spawn()
            .map(|_| "Hub restarted".to_string())
            .map_err(|e| e.to_string())
    }
}

#[tauri::command]
pub fn check_hub_status() -> bool {
    HubManager::new().is_running()
}

#[tauri::command]
pub fn start_hub() -> Result<String, String> {
    HubManager::new().start()
}

#[tauri::command]
pub fn stop_hub() -> Result<String, String> {
    HubManager::new().stop()
}

#[tauri::command]
pub fn restart_hub() -> Result<String, String> {
    HubManager::new().restart()
}
```

**Frontend Integration**:
```typescript
// src/services/hubControl.ts
import { invoke } from '@tauri-apps/api/tauri';

export const hubControl = {
  async isRunning(): Promise<boolean> {
    return await invoke('check_hub_status');
  },
  
  async start(): Promise<string> {
    return await invoke('start_hub');
  },
  
  async stop(): Promise<string> {
    return await invoke('stop_hub');
  },
  
  async restart(): Promise<string> {
    return await invoke('restart_hub');
  }
};
```

**Deliverables**:
- [ ] Rust hub management module
- [ ] Frontend hub control service
- [ ] Status polling mechanism
- [ ] Error handling and notifications

#### Task 2.3: Deprecate Python Tray App
**Duration**: 0.5 days  
**Dependencies**: Task 2.2

**Steps**:
1. Add deprecation notice to `aas_tray.py`
2. Update startup scripts to launch desktop app instead
3. Document migration path for users
4. Keep as fallback for 1 release cycle

**Deliverables**:
- [ ] Deprecation notice
- [ ] Updated documentation
- [ ] Migration guide

---

### Phase 3: Offline Mode & Caching (Week 3)
**Goal**: Enable dashboard to function without active Hub connection

#### Task 3.1: Local Data Store
**Duration**: 2 days

**Implementation**:
```typescript
// src/services/localStore.ts
import { Store } from 'tauri-plugin-store-api';

const store = new Store('.aas-cache.dat');

export const localStore = {
  async cacheTasks(tasks: Task[]) {
    await store.set('tasks', tasks);
    await store.save();
  },
  
  async getCachedTasks(): Promise<Task[]> {
    return await store.get('tasks') || [];
  },
  
  async cacheAgents(agents: Agent[]) {
    await store.set('agents', agents);
    await store.save();
  },
  
  async getOfflineMode(): Promise<boolean> {
    return await store.get('offline_mode') || false;
  }
};
```

**Deliverables**:
- [ ] Local storage implementation
- [ ] Cache invalidation strategy
- [ ] Offline indicator UI

#### Task 3.2: Connection State Management
**Duration**: 1 day  
**Dependencies**: Task 3.1

**Features**:
- Detect Hub connectivity
- Graceful fallback to cached data
- Auto-reconnect on Hub startup
- Visual offline indicators

**Deliverables**:
- [ ] Connection monitor hook
- [ ] Reconnection logic
- [ ] UI status indicators

---

### Phase 4: Distribution & Updates (Week 4)
**Goal**: Professional packaging and auto-update support

#### Task 4.1: Build Configuration
**Duration**: 1 day

**Tauri Configuration**:
```json
// tauri.conf.json
{
  "build": {
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build",
    "devPath": "http://localhost:5174",
    "distDir": "../dist"
  },
  "package": {
    "productName": "AAS Mission Control",
    "version": "1.0.0"
  },
  "tauri": {
    "bundle": {
      "identifier": "com.aaroneous.aas",
      "icon": [
        "icons/32x32.png",
        "icons/128x128.png",
        "icons/icon.icns",
        "icons/icon.ico"
      ],
      "targets": ["msi", "nsis"],
      "windows": {
        "certificateThumbprint": null,
        "digestAlgorithm": "sha256",
        "timestampUrl": ""
      }
    }
  }
}
```

**Deliverables**:
- [ ] Build scripts
- [ ] Application icons
- [ ] Windows installer configs

#### Task 4.2: Auto-Updater
**Duration**: 2 days  
**Dependencies**: Task 4.1

**Implementation**:
```rust
// src-tauri/src/main.rs
use tauri::updater::UpdaterBuilder;

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let handle = app.handle();
            tauri::async_runtime::spawn(async move {
                let updater = UpdaterBuilder::new()
                    .build()
                    .expect("Failed to build updater");
                    
                match updater.check().await {
                    Ok(update) => {
                        if update.is_update_available() {
                            update.download_and_install().await.unwrap();
                        }
                    }
                    Err(e) => println!("Update check failed: {}", e),
                }
            });
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

**Deliverables**:
- [ ] Update server configuration
- [ ] Version checking logic
- [ ] Silent update mechanism
- [ ] Release notes integration

#### Task 4.3: Code Signing & Distribution
**Duration**: 1 day  
**Dependencies**: Task 4.2

**Steps**:
1. Acquire code signing certificate (Windows)
2. Configure GitHub Actions for releases
3. Set up update server (GitHub Releases or S3)
4. Create installer branding assets

**Deliverables**:
- [ ] Signed executables
- [ ] GitHub Actions workflow
- [ ] Distribution documentation

---

### Phase 5: Polish & Testing (Week 5)
**Goal**: Production-ready quality

#### Task 5.1: Comprehensive Testing
**Duration**: 3 days

**Test Coverage**:
- [ ] Unit tests for Rust commands
- [ ] Integration tests for frontend
- [ ] E2E tests with Playwright
- [ ] Manual UAT scenarios

**Test Scenarios**:
1. Fresh install on clean Windows machine
2. Upgrade from Python tray app
3. Offline mode edge cases
4. Hub crash recovery
5. Multi-monitor support
6. High DPI displays

#### Task 5.2: Performance Optimization
**Duration**: 1 day

**Targets**:
- App launch time: <2s
- Memory usage: <150MB
- Installer size: <15MB (Tauri) or <60MB (Electron)

**Optimization**:
- Code splitting
- Lazy loading
- Asset compression
- Dead code elimination

#### Task 5.3: Documentation
**Duration**: 1 day

**Documents to Create**:
- [ ] User installation guide
- [ ] Developer build instructions
- [ ] Troubleshooting FAQ
- [ ] Release notes template

---

## Success Metrics

### Technical KPIs
- ✅ Feature parity with Python tray app
- ✅ <100ms response time for UI interactions
- ✅ <5s cold start time
- ✅ <150MB memory footprint
- ✅ Zero critical security vulnerabilities
- ✅ 90%+ test coverage

### User Experience KPIs
- ✅ One-click installation
- ✅ Silent background updates
- ✅ Native OS integration (notifications, tray)
- ✅ Offline mode functional
- ✅ <5 support tickets per 1000 installs

### Business KPIs
- ✅ Replace Python tray app completely
- ✅ Reduce startup friction by 50%
- ✅ Enable non-technical users
- ✅ Cross-platform support (Windows, macOS, Linux)

---

## Risk Management

### High Priority Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Tauri learning curve | Schedule delay | Start with Electron POC, migrate later |
| Code signing costs | Distribution blocked | Use self-signed for internal testing |
| Python-Rust interop issues | Feature gaps | Keep Python scripts as fallback |
| Update mechanism failures | User frustration | Manual download as backup |

### Medium Priority Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Large bundle size | Slow adoption | Optimize assets, use compression |
| Cross-platform bugs | Support burden | Phase releases (Windows → macOS → Linux) |
| Breaking API changes | Integration issues | Version lock critical dependencies |

---

## Post-Launch Roadmap

### v1.1 (Q2 2026)
- [ ] macOS native build
- [ ] Linux AppImage/Flatpak
- [ ] Plugin marketplace integration
- [ ] Voice command integration (Home Assistant)

### v1.2 (Q3 2026)
- [ ] Multi-Hub management
- [ ] Remote Hub control (SSH tunnel)
- [ ] Mobile companion app (React Native)
- [ ] Advanced theming engine

### v2.0 (Q4 2026)
- [ ] Visual scripting editor (from dev_studio plugin)
- [ ] Built-in terminal emulator
- [ ] Database browser
- [ ] Log analyzer with AI insights

---

## Resources Required

### Development Team
- 1 Senior Rust Developer (Tauri backend)
- 1 React Developer (Frontend migration)
- 1 QA Engineer (Testing & automation)
- 0.5 DevOps Engineer (CI/CD setup)

### Infrastructure
- Code signing certificate: $200/year
- Update server: GitHub Releases (free) or S3 ($5/month)
- CI/CD runners: GitHub Actions (free for public repos)

### Timeline
- **Total Duration**: 5 weeks
- **Estimated Effort**: 12-15 person-weeks
- **Target Release**: End of Q1 2026

---

## References

### Technical Documentation
- [Tauri Documentation](https://tauri.app/v1/guides/)
- [Electron Documentation](https://www.electronjs.org/docs/latest)
- [React Desktop Best Practices](https://reactjs.org/)

### Internal Documents
- [ROADMAP.md](ROADMAP.md) - Main project roadmap
- [WORKSPACE_STRUCTURE.md](WORKSPACE_STRUCTURE.md) - Project organization
- [AI_AGENT_GUIDELINES.md](AI_AGENT_GUIDELINES.md) - Development protocols

### Related Projects
- Project Maelstrom (C# WinForms) - Reference implementation
- `aas_tray.py` - Current tray app to replace
- `dashboard/` - Existing web UI to wrap

---

## Changelog

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-01-04 | 1.0 | Initial roadmap creation | GitHub Copilot |

---

*For questions or suggestions, see [AI_AGENT_GUIDELINES.md](AI_AGENT_GUIDELINES.md) for collaboration protocols.*
