import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  ListTodo, 
  Activity, 
  Terminal, 
  Settings, 
  Shield, 
  Zap,
  CheckCircle2,
  Clock,
  AlertCircle,
  User,
  ChevronDown,
  ChevronRight
} from 'lucide-react';

interface Task {
  id: string;
  title: string;
  priority: string;
  status: string;
  assignee: string;
  updated: string;
}

interface Agent {
  session_id: string;
  agent_name: string;
  agent_version: string;
  capabilities: {
    strengths?: string[];
    languages?: string[];
    context_window?: string;
    best_for?: string[];
  };
  current_task: string | null;
  active_tasks: number;
  last_activity: string;
}

interface OllamaModel {
  name: string;
  size: number;
  details: {
    parameter_size: string;
    quantization_level: string;
  };
}

interface Event {
  timestamp: string;
  type: string;
  message: string;
  color: string;
}

interface Batch {
  id: string;
  status: string;
  metadata: Record<string, any>;
  request_counts?: {
    total: number;
    completed: number;
    failed: number;
  };
}

function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [autoUpdate, setAutoUpdate] = useState(false);
  const [showCompletedTasks, setShowCompletedTasks] = useState(false);
  const [batches, setBatches] = useState<Batch[]>([]);
  const [batchStats, setBatchStats] = useState({ total: 0, configured: false });
  const [autoMonitorEnabled, setAutoMonitorEnabled] = useState(false);
  const [ollamaModels, setOllamaModels] = useState<OllamaModel[]>([]);
  const [ollamaStatus, setOllamaStatus] = useState<'online' | 'offline'>('offline');
  const [lmStudioStatus, setLmStudioStatus] = useState<'online' | 'offline'>('offline');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const tasksRes = await fetch('http://localhost:8000/tasks');
        const tasksData = await tasksRes.json();
        // Map backend task status to frontend Task interface if needed
        // For now, use mock if backend is empty
        if (tasksData.tasks && tasksData.tasks.length > 0) {
          setTasks(tasksData.tasks);
        } else {
          setTasks([
            { id: 'AAS-114', title: 'Implement gRPC Task Broadcasting', priority: 'High', status: 'Done', assignee: 'Sixth', updated: '2026-01-03' },
            { id: 'AAS-213', title: 'Implement Live Event Stream (WebSockets)', priority: 'High', status: 'In Progress', assignee: 'GitHub Copilot', updated: '2026-01-03' },
            { id: 'AAS-214', title: 'Scaffold Mission Control Dashboard', priority: 'High', status: 'Done', assignee: 'Sixth', updated: '2026-01-03' },
          ]);
        }

        const agentsRes = await fetch('http://localhost:8000/agents');
        const agentsData = await agentsRes.json();
        // AgentsData is an array, set it directly
        setAgents(agentsData || []);
        
        // Fetch batch status
        try {
          const batchRes = await fetch('http://localhost:8000/batch/status');
          if (batchRes.ok) {
            const batchData = await batchRes.json();
            setBatches(batchData.active_batches || []);
            setBatchStats({ total: (batchData.active_batches || []).length, configured: batchData.configured || false });
            // Set auto-monitor status from batch status response
            if (batchData.auto_monitor_enabled !== undefined) {
              setAutoMonitorEnabled(batchData.auto_monitor_enabled);
            }
          }
        } catch {
          setBatchStats({ total: 0, configured: false });
        }

        // Fetch Ollama status
        try {
          const ollamaRes = await fetch('http://localhost:11434/api/tags');
          if (ollamaRes.ok) {
            const data = await ollamaRes.json();
            setOllamaModels(data.models || []);
            setOllamaStatus('online');
          } else {
            setOllamaStatus('offline');
          }
        } catch {
          setOllamaStatus('offline');
        }

        // Fetch LM Studio status
        try {
          const lmStudioRes = await fetch('http://192.168.1.2:1234/v1/models');
          if (lmStudioRes.ok) {
            setLmStudioStatus('online');
          } else {
            setLmStudioStatus('offline');
          }
        } catch {
          setLmStudioStatus('offline');
        }
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const [events, setEvents] = useState<Event[]>([]);

  useEffect(() => {
    const socket = new WebSocket('ws://localhost:8000/ws/events');
    
    socket.onopen = () => {
      console.log("Connected to AAS WebSocket");
      setEvents(prev => [{
        timestamp: new Date().toLocaleTimeString(),
        type: 'SYSTEM',
        message: 'WebSocket connection established',
        color: 'text-emerald-400'
      }, ...prev]);
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.event_type) {
          // Task event
          setEvents(prev => [{
            timestamp: new Date().toLocaleTimeString(),
            type: 'TASK',
            message: `${data.task_id} ${data.event_type.toLowerCase()} by ${data.assignee}`,
            color: data.event_type === 'COMPLETED' ? 'text-emerald-400' : 'text-indigo-400'
          }, ...prev].slice(0, 50));

          // Refresh tasks
          fetch('http://localhost:8000/tasks')
            .then(res => res.json())
            .then(data => {
              if (data.tasks) setTasks(data.tasks);
            });
        }
      } catch (err) {
        console.error("WS Message Error:", err);
      }
    };

    socket.onclose = () => {
      console.log("Disconnected from AAS WebSocket");
    };

    return () => socket.close();
  }, []);

  // Toggle auto-monitor handler
  const toggleAutoMonitor = async () => {
    try {
      const res = await fetch('http://localhost:8000/batch/auto-monitor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: !autoMonitorEnabled })
      });
      const data = await res.json();
      if (res.ok) {
        setAutoMonitorEnabled(data.enabled);
        alert(`✅ Auto-Batch Monitor ${data.enabled ? 'enabled' : 'disabled'} - active immediately!`);
      } else {
        alert('❌ Failed to toggle auto-monitor');
      }
    } catch (e) {
      alert('❌ Failed to toggle auto-monitor');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-64 bg-slate-900 border-r border-slate-800 p-4">
        <div className="flex items-center gap-3 mb-8 px-2">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-white">AAS Hub</h1>
        </div>

        <nav className="space-y-1">
          <NavItem icon={<LayoutDashboard size={20} />} label="Overview" active={activeTab === 'overview'} onClick={() => setActiveTab('overview')} />
          <NavItem icon={<ListTodo size={20} />} label="Task Board" active={activeTab === 'tasks'} onClick={() => setActiveTab('tasks')} />
          <NavItem icon={<Activity size={20} />} label="Fleet Health" active={activeTab === 'health'} onClick={() => setActiveTab('health')} />
          <NavItem icon={<Terminal size={20} />} label="Live Console" active={activeTab === 'console'} onClick={() => setActiveTab('console')} />
          <NavItem icon={<Zap size={20} />} label="Batch Operations" active={activeTab === 'batch'} onClick={() => setActiveTab('batch')} />
          <div className="pt-4 mt-4 border-t border-slate-800">
            <NavItem icon={<Shield size={20} />} label="Security" active={activeTab === 'security'} onClick={() => setActiveTab('security')} />
            <NavItem icon={<Settings size={20} />} label="Settings" active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} />
          </div>
        </nav>

        <div className="absolute bottom-4 left-4 right-4 p-3 bg-slate-800/50 rounded-xl border border-slate-700/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-indigo-500/20 flex items-center justify-center border border-indigo-500/30">
              <User className="w-6 h-6 text-indigo-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-white">Sixth</p>
              <p className="text-xs text-slate-400">Lead Engineer</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="ml-64 p-8">
        <header className="flex justify-between items-center mb-8">
          <div>
            <h2 className="text-3xl font-bold text-white">Mission Control</h2>
            <p className="text-slate-400">Real-time fleet orchestration and monitoring</p>
          </div>
          <div className="flex gap-3">
            <div className="px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-center gap-2">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
              <span className="text-sm font-medium text-emerald-400">System Online</span>
            </div>
          </div>
        </header>

        {activeTab === 'overview' && (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <StatCard label="Active Tasks" value={tasks.filter(t => t.status !== 'Done').length.toString()} icon={<ListTodo className="text-indigo-400" />} trend="+2" />
              <StatCard label="Fleet Health" value="98%" icon={<Activity className="text-emerald-400" />} trend="Stable" />
              <StatCard label="Agents Online" value={agents.length.toString()} icon={<User className="text-amber-400" />} trend="Max" />
              <StatCard label="Uptime" value="14d 2h" icon={<Clock className="text-sky-400" />} trend="100%" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Task Board Preview */}
              <section className="lg:col-span-2 bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden">
                <div className="p-6 border-b border-slate-800 flex justify-between items-center">
                  <h3 className="text-lg font-semibold text-white">Active Task Board</h3>
                  <button onClick={() => setActiveTab('tasks')} className="text-sm text-indigo-400 hover:text-indigo-300 font-medium">View All</button>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-slate-800/30">
                        <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">ID</th>
                        <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">Task</th>
                        <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">Status</th>
                        <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">Assignee</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {tasks.slice(0, 5).map(task => (
                        <tr key={task.id} className="hover:bg-slate-800/20 transition-colors">
                          <td className="px-6 py-4 text-sm font-mono text-slate-400">{task.id}</td>
                          <td className="px-6 py-4">
                            <p className="text-sm font-medium text-white">{task.title}</p>
                            <p className="text-xs text-slate-500">{task.priority} Priority</p>
                          </td>
                          <td className="px-6 py-4">
                            <StatusBadge status={task.status} />
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-400">{task.assignee}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>

              {/* Live Feed */}
              <section className="bg-slate-900 rounded-2xl border border-slate-800 flex flex-col">
                <div className="p-6 border-b border-slate-800">
                  <h3 className="text-lg font-semibold text-white">Live Event Stream</h3>
                </div>
                <div className="flex-1 p-4 space-y-4 overflow-y-auto max-h-[500px] font-mono text-xs">
                  {events.length === 0 && (
                    <div className="p-3 bg-slate-950 rounded border border-slate-800 text-slate-400 italic">
                      Waiting for live events...
                    </div>
                  )}
                  {events.map((event, i) => (
                    <div key={i} className={`p-3 bg-slate-950 rounded border border-slate-800 ${event.color}`}>
                      <span className="text-slate-600">[{event.timestamp}]</span> {event.type}: {event.message}
                    </div>
                  ))}
                </div>
              </section>
            </div>
          </>
        )}

        {activeTab === 'tasks' && (
          <div className="space-y-6">
            {/* Active Tasks */}
            <section className="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden">
              <div className="p-6 border-b border-slate-800">
                <h3 className="text-lg font-semibold text-white">Active Tasks ({tasks.filter(t => t.status.toLowerCase() !== 'done').length})</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-800/30">
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">ID</th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">Task</th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">Status</th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">Assignee</th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">Updated</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {tasks.filter(t => t.status.toLowerCase() !== 'done').map(task => (
                      <tr key={task.id} className="hover:bg-slate-800/20 transition-colors">
                        <td className="px-6 py-4 text-sm font-mono text-slate-400">{task.id}</td>
                        <td className="px-6 py-4">
                          <p className="text-sm font-medium text-white">{task.title}</p>
                          <p className="text-xs text-slate-500">{task.priority} Priority</p>
                        </td>
                        <td className="px-6 py-4">
                          <StatusBadge status={task.status} />
                        </td>
                        <td className="px-6 py-4 text-sm text-slate-400">{task.assignee}</td>
                        <td className="px-6 py-4 text-sm text-slate-500">{task.updated}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            {/* Completed Tasks - Collapsible */}
            <section className="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden">
              <button 
                onClick={() => setShowCompletedTasks(!showCompletedTasks)}
                className="w-full p-6 flex items-center justify-between hover:bg-slate-800/30 transition-colors"
              >
                <div className="flex items-center gap-3">
                  {showCompletedTasks ? <ChevronDown size={20} className="text-slate-400" /> : <ChevronRight size={20} className="text-slate-400" />}
                  <h3 className="text-lg font-semibold text-white">Completed Tasks ({tasks.filter(t => t.status.toLowerCase() === 'done').length})</h3>
                </div>
                <div className="flex items-center gap-2 text-sm text-emerald-400">
                  <CheckCircle2 size={16} />
                  <span>{tasks.filter(t => t.status.toLowerCase() === 'done').length} Done</span>
                </div>
              </button>
              
              {showCompletedTasks && (
                <div className="border-t border-slate-800 overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-slate-800/30">
                        <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">ID</th>
                        <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">Task</th>
                        <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">Status</th>
                        <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">Assignee</th>
                        <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">Updated</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {tasks.filter(t => t.status.toLowerCase() === 'done').map(task => (
                        <tr key={task.id} className="hover:bg-slate-800/20 transition-colors opacity-60">
                          <td className="px-6 py-4 text-sm font-mono text-slate-400">{task.id}</td>
                          <td className="px-6 py-4">
                            <p className="text-sm font-medium text-white">{task.title}</p>
                            <p className="text-xs text-slate-500">{task.priority} Priority</p>
                          </td>
                          <td className="px-6 py-4">
                            <StatusBadge status={task.status} />
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-400">{task.assignee}</td>
                          <td className="px-6 py-4 text-sm text-slate-500">{task.updated}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </div>
        )}

        {activeTab === 'console' && (
          <section className="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden">
            <div className="p-6 border-b border-slate-800">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Terminal className="text-sky-400" size={24} />
                  <h3 className="text-lg font-semibold text-white">Live Console Stream</h3>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                  <span className="text-xs text-emerald-400 font-bold">LIVE</span>
                </div>
              </div>
            </div>
            <div className="p-6 bg-slate-950 overflow-auto" style={{ maxHeight: '70vh' }}>
              {events.length === 0 ? (
                <div className="text-center py-12">
                  <Terminal className="mx-auto text-slate-600 mb-4" size={48} />
                  <p className="text-slate-500 italic">Waiting for events...</p>
                  <p className="text-xs text-slate-600 mt-2">WebSocket connected to ws://localhost:8000/ws/events</p>
                </div>
              ) : (
                <div className="space-y-2 font-mono text-sm">
                  {events.map((event, idx) => (
                    <div key={idx} className="flex items-start gap-3 p-2 hover:bg-slate-900/50 rounded transition-colors">
                      <span className="text-slate-600 text-xs shrink-0">{event.timestamp}</span>
                      <span className={`text-xs font-bold shrink-0 ${
                        event.type === 'SYSTEM' ? 'text-cyan-400' : 
                        event.type === 'TASK' ? 'text-indigo-400' : 
                        event.type === 'AGENT' ? 'text-purple-400' : 
                        'text-slate-400'
                      }`}>[{event.type}]</span>
                      <span className={`${event.color} flex-1`}>{event.message}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>
        )}

        {activeTab === 'batch' && (
          <div className="space-y-6">
            {/* Batch Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800">
                <div className="flex items-center gap-3 mb-2">
                  <Zap className="text-amber-400" size={24} />
                  <h3 className="text-sm font-medium text-slate-400">Active Batches</h3>
                </div>
                <p className="text-3xl font-bold text-white">{batchStats.total}</p>
              </div>
              
              <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800">
                <div className="flex items-center gap-3 mb-2">
                  {batchStats.configured ? (
                    <CheckCircle2 className="text-emerald-400" size={24} />
                  ) : (
                    <AlertCircle className="text-amber-400" size={24} />
                  )}
                  <h3 className="text-sm font-medium text-slate-400">API Status</h3>
                </div>
                <p className={`text-2xl font-bold ${batchStats.configured ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {batchStats.configured ? 'Configured' : 'Not Configured'}
                </p>
              </div>
              
              <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800">
                <div className="flex items-center gap-3 mb-2">
                  <Activity className="text-indigo-400" size={24} />
                  <h3 className="text-sm font-medium text-slate-400">Cost Savings</h3>
                </div>
                <p className="text-3xl font-bold text-emerald-400">50%</p>
                <p className="text-xs text-slate-500 mt-1">≤24h completion</p>
              </div>
            </div>

            {/* Submit Batch Section */}
            <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-semibold text-white">Submit New Batch</h3>
                  <p className="text-sm text-slate-400 mt-1">✨ Completes within 24 hours • 50% cost savings • Submit more for maximum efficiency</p>
                </div>
                <button 
                  onClick={async () => {
                    try {
                      const res = await fetch('http://localhost:8000/batch/submit', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ max_tasks: 50 })
                      });
                      const data = await res.json();
                      alert(data.batch_id ? `✅ Batch submitted: ${data.batch_id}` : data.message || 'No tasks eligible');
                    } catch (e) {
                      alert('❌ Failed to submit batch');
                    }
                  }}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                >
                  <Zap size={18} />
                  Submit Batch (Up to 50)
                </button>
              </div>
              
              <div className="grid grid-cols-3 gap-4 p-4 bg-slate-800/30 rounded-xl">
                <div>
                  <p className="text-xs text-slate-500 mb-1">Endpoint</p>
                  <p className="text-sm text-slate-300 font-mono">/v1/chat/completions</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Completion Window</p>
                  <p className="text-sm text-emerald-400 font-semibold">≤24 hours guaranteed</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Recommended Practice</p>
                  <p className="text-sm text-indigo-400 font-semibold">Batch aggressively</p>
                </div>
              </div>
            </section>

            {/* Auto-Monitor Toggle Section */}
            <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-white">Auto-Batch Monitor</h3>
                  <p className="text-sm text-slate-400 mt-1">Automatically submit batches when 3+ eligible tasks detected (scans every 60s)</p>
                </div>
                <button
                  onClick={toggleAutoMonitor}
                  className={`relative w-14 h-7 rounded-full transition-colors ${
                    autoMonitorEnabled ? 'bg-indigo-600' : 'bg-slate-700'
                  }`}
                >
                  <div className={`absolute top-1 w-5 h-5 bg-white rounded-full transition-transform ${
                    autoMonitorEnabled ? 'right-1' : 'left-1'
                  }`} />
                </button>
              </div>
              <div className="mt-4 p-3 bg-slate-800/30 rounded-lg border border-slate-700/50">
                <p className="text-xs text-slate-400">
                  <span className={`font-bold ${autoMonitorEnabled ? 'text-emerald-400' : 'text-amber-400'}`}>
                    Status: {autoMonitorEnabled ? 'ENABLED' : 'DISABLED'}
                  </span>
                  {' • '}
                  {autoMonitorEnabled 
                    ? 'Background monitor will automatically batch unbatched tasks' 
                    : 'Manual batch submission only'}
                </p>
              </div>
            </section>

            {/* Active Batches List */}
            <section className="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden">
              <div className="p-6 border-b border-slate-800">
                <h3 className="text-lg font-semibold text-white">Active Batches ({batches.length})</h3>
              </div>
              <div className="p-6">
                {batches.length === 0 ? (
                  <div className="text-center py-12">
                    <Zap className="mx-auto text-slate-600 mb-4" size={48} />
                    <p className="text-slate-500 italic">No active batches</p>
                    <p className="text-xs text-slate-600 mt-2">Submit tasks for batch processing above</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {batches.map(batch => (
                      <div key={batch.id} className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <Activity className="text-indigo-400" size={20} />
                            <div>
                              <h4 className="font-bold text-white font-mono text-sm">{batch.id}</h4>
                              <p className="text-xs text-slate-400">Status: {batch.status}</p>
                            </div>
                          </div>
                          <span className={`px-3 py-1 rounded-full text-xs font-bold border ${
                            batch.status === 'completed' ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' :
                            batch.status === 'in_progress' ? 'bg-indigo-500/10 text-indigo-500 border-indigo-500/20' :
                            'bg-amber-500/10 text-amber-500 border-amber-500/20'
                          }`}>
                            {batch.status.toUpperCase()}
                          </span>
                        </div>
                        
                        {batch.request_counts && (
                          <div className="grid grid-cols-3 gap-4 text-sm">
                            <div>
                              <p className="text-slate-500 text-xs mb-1">Total</p>
                              <p className="text-white font-mono">{batch.request_counts.total}</p>
                            </div>
                            <div>
                              <p className="text-slate-500 text-xs mb-1">Completed</p>
                              <p className="text-emerald-400 font-mono">{batch.request_counts.completed}</p>
                            </div>
                            <div>
                              <p className="text-slate-500 text-xs mb-1">Failed</p>
                              <p className="text-rose-400 font-mono">{batch.request_counts.failed}</p>
                            </div>
                          </div>
                        )}
                        
                        {batch.request_counts && batch.request_counts.total > 0 && (
                          <div className="mt-3">
                            <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-indigo-500 transition-all duration-500"
                                style={{ width: `${(batch.request_counts.completed / batch.request_counts.total) * 100}%` }}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </section>
          </div>
        )}

        {activeTab === 'health' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
              <h3 className="text-lg font-semibold text-white mb-6">Active Agent Fleet</h3>
              <div className="space-y-6">
                {agents.length === 0 && <p className="text-slate-500 italic">No agents currently online</p>}
                {agents.map(agent => (
                  <div key={agent.session_id} className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-indigo-500/20 flex items-center justify-center border border-indigo-500/30">
                          <User className="w-6 h-6 text-indigo-400" />
                        </div>
                        <div>
                          <h4 className="font-bold text-white">{agent.agent_name}</h4>
                          <p className="text-xs text-slate-400">{agent.session_id}</p>
                        </div>
                      </div>
                      <span className="px-2 py-1 bg-emerald-500/10 text-emerald-500 text-[10px] font-bold rounded uppercase tracking-wider border border-emerald-500/20">Active</span>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                      <div>
                        <p className="text-slate-500 text-xs mb-1">Current Task</p>
                        <p className="text-slate-200 font-mono">{agent.current_task || 'Idle'}</p>
                      </div>
                      <div>
                        <p className="text-slate-500 text-xs mb-1">Active Tasks</p>
                        <p className="text-slate-200">{agent.active_tasks}</p>
                      </div>
                    </div>
                    <div>
                      <p className="text-slate-500 text-xs mb-2">Capabilities</p>
                      <div className="flex flex-wrap gap-2">
                        {agent.capabilities?.strengths?.map((s: string) => (
                          <span key={s} className="px-2 py-0.5 bg-slate-700 text-slate-300 text-[10px] rounded border border-slate-600">{s}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
            
            <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
              <h3 className="text-lg font-semibold text-white mb-6">System Health Metrics</h3>
              <div className="space-y-4">
                <HealthMetric label="CPU Usage" value="12%" progress={12} color="bg-indigo-500" />
                <HealthMetric label="Memory Usage" value="45%" progress={45} color="bg-sky-500" />
                <HealthMetric label="Network Latency" value="24ms" progress={15} color="bg-emerald-500" />
                <HealthMetric label="Database Load" value="8%" progress={8} color="bg-amber-500" />
              </div>
            </section>
          </div>
        )}

        {activeTab === 'security' && (
          <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
            <h3 className="text-lg font-semibold text-white mb-6">Security Overview</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
                <div className="flex items-center gap-3 mb-2">
                  <Shield className="text-emerald-400" size={20} />
                  <h4 className="font-bold text-white">Firewall</h4>
                </div>
                <p className="text-sm text-slate-400">Active and monitoring incoming traffic.</p>
              </div>
              <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
                <div className="flex items-center gap-3 mb-2">
                  <Shield className="text-indigo-400" size={20} />
                  <h4 className="font-bold text-white">Encryption</h4>
                </div>
                <p className="text-sm text-slate-400">AES-256 encryption enabled for all data.</p>
              </div>
              <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
                <div className="flex items-center gap-3 mb-2">
                  <Shield className="text-amber-400" size={20} />
                  <h4 className="font-bold text-white">Access Control</h4>
                </div>
                <p className="text-sm text-slate-400">RBAC policies are strictly enforced.</p>
              </div>
            </div>
          </section>
        )}

        {activeTab === 'settings' && (
          <div className="space-y-8">
          <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
            <h3 className="text-lg font-semibold text-white mb-6">System Settings</h3>
            <div className="space-y-6 max-w-2xl">
              <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl border border-slate-700">
                <div>
                  <h4 className="font-bold text-white">Debug Mode</h4>
                  <p className="text-sm text-slate-400">Enable verbose logging for troubleshooting.</p>
                </div>
                <div className="w-12 h-6 bg-indigo-600 rounded-full relative">
                  <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full" />
                </div>
              </div>
              <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl border border-slate-700">
                <div>
                  <h4 className="font-bold text-white">Auto-Update</h4>
                  <p className="text-sm text-slate-400">Automatically install security patches.</p>
                </div>
                <button 
                  onClick={() => setAutoUpdate(!autoUpdate)}
                  className={`w-12 h-6 rounded-full relative transition-colors ${autoUpdate ? 'bg-emerald-600' : 'bg-slate-700'}`}
                >
                  <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${autoUpdate ? 'right-1' : 'left-1'}`} />
                </button>
              </div>
              <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
                <h4 className="font-bold text-white mb-2">API Endpoint</h4>
                <input 
                  type="text" 
                  readOnly 
                  value="http://localhost:8000" 
                  className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-sm font-mono text-indigo-400"
                />
              </div>
            </div>
          </section>

          <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold text-white">Local LM Server (Ollama)</h3>
              <div className={`px-3 py-1 rounded-full text-xs font-bold border ${
                ollamaStatus === 'online' 
                  ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' 
                  : 'bg-rose-500/10 text-rose-500 border-rose-500/20'
              }`}>
                {ollamaStatus.toUpperCase()}
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {ollamaModels.length === 0 && (
                <p className="text-slate-500 italic col-span-full">No local models found.</p>
              )}
              {ollamaModels.map(model => (
                <div key={model.name} className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
                  <div className="flex items-center gap-3 mb-2">
                    <Zap className="text-indigo-400" size={18} />
                    <h4 className="font-bold text-white truncate">{model.name}</h4>
                  </div>
                  <div className="text-xs text-slate-400 space-y-1">
                    <p>Size: {(model.size / 1024 / 1024 / 1024).toFixed(2)} GB</p>
                    <p>Params: {model.details.parameter_size}</p>
                    <p>Quant: {model.details.quantization_level}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold text-white">LM Studio Server</h3>
              <div className={`px-3 py-1 rounded-full text-xs font-bold border ${
                lmStudioStatus === 'online' 
                  ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' 
                  : 'bg-rose-500/10 text-rose-500 border-rose-500/20'
              }`}>
                {lmStudioStatus.toUpperCase()}
              </div>
            </div>
            <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
              <div className="flex items-center gap-3 mb-2">
                <Terminal className="text-sky-400" size={18} />
                <h4 className="font-bold text-white">Endpoint</h4>
              </div>
              <p className="text-sm text-slate-400 font-mono">http://192.168.1.2:1234</p>
            </div>
          </section>
          </div>
        )}
      </main>
    </div>
  );
}

function NavItem({ icon, label, active, onClick }: { icon: React.ReactNode, label: string, active?: boolean, onClick: () => void }) {
  return (
    <button 
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-all ${
        active 
          ? 'bg-indigo-600/10 text-indigo-400 border border-indigo-600/20' 
          : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
      }`}
    >
      {icon}
      <span className="text-sm font-medium">{label}</span>
    </button>
  );
}

function StatCard({ label, value, icon, trend }: { label: string, value: string, icon: React.ReactNode, trend: string }) {
  return (
    <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800">
      <div className="flex justify-between items-start mb-4">
        <div className="p-2 bg-slate-800 rounded-lg">
          {icon}
        </div>
        <span className={`text-xs font-bold px-2 py-1 rounded-full ${
          trend.startsWith('+') || trend === 'Stable' || trend === '100%' || trend === 'Max'
            ? 'bg-emerald-500/10 text-emerald-500'
            : 'bg-amber-500/10 text-amber-500'
        }`}>
          {trend}
        </span>
      </div>
      <p className="text-slate-400 text-sm font-medium mb-1">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  );
}

function HealthMetric({ label, value, progress, color }: { label: string, value: string, progress: number, color: string }) {
  return (
    <div>
      <div className="flex justify-between text-sm mb-2">
        <span className="text-slate-400">{label}</span>
        <span className="text-white font-medium">{value}</span>
      </div>
      <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
        <div className={`h-full ${color} transition-all duration-500`} style={{ width: `${progress}%` }} />
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles = {
    'Done': 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
    'In Progress': 'bg-indigo-500/10 text-indigo-500 border-indigo-500/20',
    'Queued': 'bg-slate-500/10 text-slate-500 border-slate-800',
    'Error': 'bg-rose-500/10 text-rose-500 border-rose-500/20',
  }[status] || 'bg-slate-500/10 text-slate-500 border-slate-800';

  const Icon = {
    'Done': CheckCircle2,
    'In Progress': Activity,
    'Queued': Clock,
    'Error': AlertCircle,
  }[status] || Clock;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold border ${styles}`}>
      <Icon size={12} />
      {status}
    </span>
  );
}

export default App;
