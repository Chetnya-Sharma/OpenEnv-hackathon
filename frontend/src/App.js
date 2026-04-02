import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import sql from 'react-syntax-highlighter/dist/esm/languages/hljs/sql';
import { atomOneLight } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import {
  Database, Play, ArrowClockwise, CheckCircle, XCircle,
  WarningCircle, SkipForward, Lightning, Clock, ChartBar,
  ListChecks, CaretRight, Shield, Gauge, Bug, ArrowRight
} from '@phosphor-icons/react';
import './App.css';

SyntaxHighlighter.registerLanguage('sql', sql);

const API = process.env.REACT_APP_BACKEND_URL;

const TASKS = [
  { id: 'single_review', name: 'Single Query Review', difficulty: 'EASY', steps: 5, queries: 1, desc: 'Review one SQL query for correctness, security, and performance' },
  { id: 'batch_review', name: 'Batch Query Review', difficulty: 'MEDIUM', steps: 25, queries: 8, desc: 'Review 8 mixed SQL queries across all issue types' },
  { id: 'pipeline_review', name: 'Pipeline Review', difficulty: 'HARD', steps: 50, queries: 15, desc: 'Review 15 queries with prioritization and urgent flags' },
];

const ISSUE_OPTIONS = [
  { value: 'sql_injection', label: 'SQL Injection', icon: Shield },
  { value: 'performance', label: 'Performance', icon: Gauge },
  { value: 'logic_bug', label: 'Logic Bug', icon: Bug },
  { value: 'missing_index', label: 'Missing Index', icon: Database },
  { value: 'n_plus_one', label: 'N+1 Query', icon: Lightning },
  { value: 'no_issues', label: 'No Issues', icon: CheckCircle },
];

function Badge({ children, color = 'default' }) {
  const colors = {
    default: 'border-black text-black',
    approve: 'border-[#00C853] text-[#00C853] bg-[#00C853]/5',
    reject: 'border-[#FF2A00] text-[#FF2A00] bg-[#FF2A00]/5',
    changes: 'border-[#FF8C00] text-[#FF8C00] bg-[#FF8C00]/5',
    skip: 'border-[#71717A] text-[#71717A]',
    easy: 'border-[#00C853] text-[#00C853]',
    medium: 'border-[#FF8C00] text-[#FF8C00]',
    hard: 'border-[#FF2A00] text-[#FF2A00]',
    urgent: 'border-[#FF2A00] text-[#FF2A00] bg-[#FF2A00]/10',
    primary: 'border-[#002FA7] text-[#002FA7]',
  };
  return (
    <span data-testid={`badge-${color}`} className={`inline-flex items-center border px-2 py-0.5 text-xs font-bold uppercase tracking-[0.15em] ${colors[color] || colors.default}`}>
      {children}
    </span>
  );
}

function Metric({ label, value, sub }) {
  return (
    <div className="flex flex-col" data-testid={`metric-${label.toLowerCase().replace(/\s+/g, '-')}`}>
      <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#A1A1AA]">{label}</span>
      <span className="text-2xl font-black tracking-tighter font-[Chivo]">{value}</span>
      {sub && <span className="text-xs text-[#52525B]">{sub}</span>}
    </div>
  );
}

export default function App() {
  const [selectedTask, setSelectedTask] = useState(null);
  const [observation, setObservation] = useState(null);
  const [envInfo, setEnvInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [currentQueryIdx, setCurrentQueryIdx] = useState(0);
  const [selectedIssues, setSelectedIssues] = useState([]);
  const [suggestedFix, setSuggestedFix] = useState('');
  const [confidence, setConfidence] = useState(0.8);
  const [totalReward, setTotalReward] = useState(0);
  const [lastReward, setLastReward] = useState(null);
  const [queryStats, setQueryStats] = useState(null);
  const historyEndRef = useRef(null);

  useEffect(() => {
    fetch(`${API}/api/env/queries`).then(r => r.json()).then(setQueryStats).catch(() => {});
  }, []);

  useEffect(() => {
    if (historyEndRef.current) historyEndRef.current.scrollIntoView({ behavior: 'smooth' });
  }, [history]);

  const resetEnv = useCallback(async (taskId) => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/env/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_id: taskId }),
      });
      const data = await res.json();
      setObservation(data.observation);
      setEnvInfo(data.info);
      setHistory([]);
      setCurrentQueryIdx(0);
      setSelectedIssues([]);
      setSuggestedFix('');
      setTotalReward(0);
      setLastReward(null);
      setSelectedTask(taskId);
    } catch (e) {
      console.error('Reset failed:', e);
    }
    setLoading(false);
  }, []);

  const takeAction = useCallback(async (actionType, verdict) => {
    if (!observation || observation.done) return;
    const queries = observation.queries || [];
    if (queries.length === 0) return;

    const query = queries[currentQueryIdx] || queries[0];
    setLoading(true);

    const action = {
      action_type: actionType,
      query_id: query.query_id,
      verdict: verdict || (actionType === 'approve' ? 'approve' : actionType === 'reject' ? 'reject' : null),
      issues_found: selectedIssues.length > 0 ? selectedIssues : ['no_issues'],
      suggested_fix: suggestedFix,
      confidence: confidence,
    };

    try {
      const res = await fetch(`${API}/api/env/step`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(action),
      });
      const data = await res.json();
      setObservation(data.observation);
      setLastReward(data.reward);
      setTotalReward(prev => prev + data.reward);
      setHistory(prev => [...prev, {
        step: data.observation.current_step,
        queryId: query.query_id,
        action: actionType,
        verdict: action.verdict,
        reward: data.reward,
        done: data.done,
        issues: action.issues_found,
      }]);

      // Advance to next unreviewed query
      if (!data.done && data.observation.queries) {
        const reviewedIds = new Set(history.map(h => h.queryId));
        reviewedIds.add(query.query_id);
        const nextIdx = data.observation.queries.findIndex(q => !reviewedIds.has(q.query_id));
        setCurrentQueryIdx(nextIdx >= 0 ? nextIdx : 0);
      }

      setSelectedIssues([]);
      setSuggestedFix('');
    } catch (e) {
      console.error('Step failed:', e);
    }
    setLoading(false);
  }, [observation, currentQueryIdx, selectedIssues, suggestedFix, confidence, history]);

  const toggleIssue = (issue) => {
    if (issue === 'no_issues') {
      setSelectedIssues(['no_issues']);
      return;
    }
    setSelectedIssues(prev => {
      const filtered = prev.filter(i => i !== 'no_issues');
      if (filtered.includes(issue)) return filtered.filter(i => i !== issue);
      return [...filtered, issue];
    });
  };

  const currentQueries = observation?.queries || [];
  const currentQuery = currentQueries[currentQueryIdx];
  const isDone = observation?.done;

  // Task Selection Screen
  if (!selectedTask || !observation) {
    return (
      <div className="min-h-screen bg-white" data-testid="task-selection-screen">
        {/* Header */}
        <div className="border-b border-[#E4E4E7]">
          <div className="max-w-7xl mx-auto px-8 py-6 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Database size={28} weight="bold" />
              <h1 className="text-2xl font-black tracking-tighter uppercase font-[Chivo]" data-testid="app-title">
                SQL Review Env
              </h1>
            </div>
            {queryStats && (
              <div className="flex gap-6">
                <Metric label="Total Queries" value={queryStats.total} />
                <Metric label="Safe" value={queryStats.categories?.safe} />
                <Metric label="Injection" value={queryStats.categories?.injection} />
                <Metric label="Performance" value={queryStats.categories?.performance} />
                <Metric label="Logic Bug" value={queryStats.categories?.logic_bug} />
              </div>
            )}
          </div>
        </div>

        {/* Task Cards */}
        <div className="max-w-7xl mx-auto px-8 py-12">
          <div className="mb-8">
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#A1A1AA]">Select Task</span>
            <h2 className="text-4xl font-black tracking-tighter uppercase font-[Chivo] mt-1" data-testid="select-task-heading">
              Choose Your Challenge
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 border border-[#E4E4E7]">
            {TASKS.map((task, i) => (
              <button
                key={task.id}
                data-testid={`select-task-${task.id}`}
                onClick={() => resetEnv(task.id)}
                disabled={loading}
                className={`text-left p-8 border-r border-[#E4E4E7] last:border-r-0 transition-colors duration-150 hover:bg-[#F4F4F5] active:bg-[#E4E4E7] disabled:opacity-50 flex flex-col gap-4`}
              >
                <div className="flex items-center justify-between">
                  <Badge color={task.difficulty.toLowerCase()}>{task.difficulty}</Badge>
                  <ArrowRight size={20} className="text-[#A1A1AA]" />
                </div>
                <h3 className="text-lg font-bold tracking-tight font-[Chivo]">{task.name}</h3>
                <p className="text-sm text-[#52525B] leading-relaxed">{task.desc}</p>
                <div className="flex gap-6 mt-auto pt-4 border-t border-[#E4E4E7]">
                  <div>
                    <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#A1A1AA]">Steps</span>
                    <p className="text-lg font-black font-[Chivo]">{task.steps}</p>
                  </div>
                  <div>
                    <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#A1A1AA]">Queries</span>
                    <p className="text-lg font-black font-[Chivo]">{task.queries}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>

          {/* Environment Info */}
          <div className="mt-12 border border-[#E4E4E7] p-8">
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#A1A1AA]">About</span>
            <h3 className="text-lg font-bold tracking-tight font-[Chivo] mt-1 mb-3">OpenEnv SQL Review Environment</h3>
            <p className="text-sm text-[#52525B] leading-relaxed max-w-3xl">
              An AI agent training environment for SQL query review. Agents must identify SQL injection risks,
              performance issues, and logic bugs in queries — then approve or reject them for production deployment.
              Graders are 100% deterministic with rich partial reward signals across multiple quality dimensions.
            </p>
            <div className="flex gap-4 mt-4">
              <Badge color="primary">OPENENV</Badge>
              <Badge>V1.0.0</Badge>
              <Badge>56 QUERIES</Badge>
              <Badge>3 TASKS</Badge>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Review Dashboard
  return (
    <div className="min-h-screen bg-white flex flex-col" data-testid="review-dashboard">
      {/* Top Bar */}
      <div className="border-b border-[#E4E4E7] flex items-center justify-between px-6 py-3">
        <div className="flex items-center gap-4">
          <button
            data-testid="btn-back"
            onClick={() => { setSelectedTask(null); setObservation(null); }}
            className="border border-black px-4 py-1.5 text-xs font-bold uppercase tracking-widest hover:bg-[#F4F4F5] transition-colors duration-150"
          >
            Back
          </button>
          <div className="flex items-center gap-2">
            <Database size={20} weight="bold" />
            <span className="font-bold font-[Chivo] tracking-tight uppercase">{selectedTask.replace('_', ' ')}</span>
          </div>
          <Badge color={TASKS.find(t => t.id === selectedTask)?.difficulty.toLowerCase()}>
            {TASKS.find(t => t.id === selectedTask)?.difficulty}
          </Badge>
        </div>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 text-sm">
            <Clock size={16} />
            <span className="font-mono text-sm">Step {observation.current_step}/{envInfo?.max_steps || '—'}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <ListChecks size={16} />
            <span className="font-mono text-sm">{observation.reviewed_count}/{(observation.reviewed_count + observation.pending_count)}</span>
          </div>
          {isDone && <Badge color="approve">COMPLETE</Badge>}
          <button
            data-testid="btn-reset"
            onClick={() => resetEnv(selectedTask)}
            disabled={loading}
            className="border border-black px-4 py-1.5 text-xs font-bold uppercase tracking-widest hover:bg-[#F4F4F5] transition-colors duration-150 flex items-center gap-1.5"
          >
            <ArrowClockwise size={14} /> Reset
          </button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="flex-1 grid grid-cols-12 border-t border-[#E4E4E7]" style={{ minHeight: 'calc(100vh - 52px)' }}>
        {/* Left: Query List */}
        <div className="col-span-2 border-r border-[#E4E4E7] overflow-y-auto" data-testid="query-list">
          <div className="p-4 border-b border-[#E4E4E7]">
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#A1A1AA]">Queries</span>
          </div>
          {currentQueries.map((q, i) => {
            const reviewed = history.some(h => h.queryId === q.query_id);
            const isActive = i === currentQueryIdx;
            return (
              <button
                key={q.query_id}
                data-testid={`query-item-${q.query_id}`}
                onClick={() => setCurrentQueryIdx(i)}
                className={`w-full text-left px-4 py-3 border-b border-[#E4E4E7] transition-colors duration-150 ${isActive ? 'bg-[#F4F4F5]' : 'hover:bg-[#F4F4F5]/50'}`}
              >
                <div className="flex items-center gap-2">
                  {reviewed ? (
                    <CheckCircle size={14} weight="fill" className="text-[#00C853] flex-shrink-0" />
                  ) : (
                    <CaretRight size={14} className="text-[#A1A1AA] flex-shrink-0" />
                  )}
                  <span className="font-mono text-xs truncate">{q.query_id}</span>
                </div>
                <div className="flex items-center gap-2 mt-1 ml-5">
                  <span className="text-[10px] uppercase tracking-wider text-[#A1A1AA]">{q.query_type}</span>
                  {q.is_urgent && <Badge color="urgent">URGENT</Badge>}
                </div>
              </button>
            );
          })}
        </div>

        {/* Center: Query Viewer + Action */}
        <div className="col-span-7 border-r border-[#E4E4E7] flex flex-col overflow-y-auto">
          {currentQuery ? (
            <>
              {/* Query Header */}
              <div className="px-6 py-4 border-b border-[#E4E4E7] flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-sm font-bold">{currentQuery.query_id}</span>
                    <Badge>{currentQuery.query_type}</Badge>
                    {currentQuery.is_urgent && <Badge color="urgent">URGENT</Badge>}
                  </div>
                  <div className="flex items-center gap-4 mt-1 text-xs text-[#52525B]">
                    <span>by {currentQuery.submitted_by}</span>
                    <span>db: {currentQuery.database}</span>
                  </div>
                </div>
              </div>

              {/* SQL Code */}
              <div className="px-6 py-4 border-b border-[#E4E4E7] flex-shrink-0" data-testid="sql-viewer">
                <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#A1A1AA] mb-3 block">SQL Query</span>
                <div className="border border-[#E4E4E7] bg-[#FAFAFA]">
                  <SyntaxHighlighter
                    language="sql"
                    style={atomOneLight}
                    customStyle={{
                      margin: 0,
                      padding: '1.5rem',
                      background: '#FAFAFA',
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: '0.875rem',
                      lineHeight: '1.7',
                    }}
                    showLineNumbers
                    lineNumberStyle={{ color: '#A1A1AA', fontSize: '0.75rem', paddingRight: '1rem' }}
                  >
                    {currentQuery.sql}
                  </SyntaxHighlighter>
                </div>
              </div>

              {/* Issue Selection */}
              {!isDone && (
                <div className="px-6 py-4 border-b border-[#E4E4E7]" data-testid="issue-selection">
                  <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#A1A1AA] mb-3 block">Issues Found</span>
                  <div className="flex flex-wrap gap-2">
                    {ISSUE_OPTIONS.map(opt => {
                      const Icon = opt.icon;
                      const isSelected = selectedIssues.includes(opt.value);
                      return (
                        <button
                          key={opt.value}
                          data-testid={`issue-${opt.value}`}
                          onClick={() => toggleIssue(opt.value)}
                          className={`flex items-center gap-1.5 border px-3 py-1.5 text-xs font-bold uppercase tracking-widest transition-colors duration-150 ${isSelected ? 'bg-black text-white border-black' : 'border-[#E4E4E7] text-[#52525B] hover:border-black'}`}
                        >
                          <Icon size={14} /> {opt.label}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Suggested Fix */}
              {!isDone && (
                <div className="px-6 py-4 border-b border-[#E4E4E7]" data-testid="fix-input">
                  <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#A1A1AA] mb-2 block">Suggested Fix</span>
                  <textarea
                    data-testid="suggested-fix-textarea"
                    value={suggestedFix}
                    onChange={e => setSuggestedFix(e.target.value)}
                    placeholder="Enter corrected SQL query..."
                    className="w-full border border-[#E4E4E7] bg-[#FAFAFA] p-4 font-mono text-sm resize-none h-24 focus:border-black focus:ring-2 focus:ring-black focus:ring-offset-2 focus:outline-none"
                  />
                </div>
              )}

              {/* Confidence Slider */}
              {!isDone && (
                <div className="px-6 py-4 border-b border-[#E4E4E7] flex items-center gap-4">
                  <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#A1A1AA]">Confidence</span>
                  <input
                    data-testid="confidence-slider"
                    type="range" min="0" max="1" step="0.05"
                    value={confidence}
                    onChange={e => setConfidence(parseFloat(e.target.value))}
                    className="flex-1 accent-black"
                  />
                  <span className="font-mono text-sm font-bold w-12 text-right">{confidence.toFixed(2)}</span>
                </div>
              )}

              {/* Action Buttons */}
              {!isDone && (
                <div className="px-6 py-4 flex gap-3" data-testid="action-buttons">
                  <button
                    data-testid="btn-approve"
                    onClick={() => takeAction('approve', 'approve')}
                    disabled={loading}
                    className="flex-1 border-2 border-[#00C853] text-[#00C853] px-6 py-3 text-sm font-bold uppercase tracking-widest transition-colors duration-150 hover:bg-[#00C853] hover:text-white disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    <CheckCircle size={18} weight="bold" /> Approve
                  </button>
                  <button
                    data-testid="btn-reject"
                    onClick={() => takeAction('reject', 'reject')}
                    disabled={loading}
                    className="flex-1 border-2 border-[#FF2A00] text-[#FF2A00] px-6 py-3 text-sm font-bold uppercase tracking-widest transition-colors duration-150 hover:bg-[#FF2A00] hover:text-white disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    <XCircle size={18} weight="bold" /> Reject
                  </button>
                  <button
                    data-testid="btn-request-changes"
                    onClick={() => takeAction('request_changes', 'reject')}
                    disabled={loading}
                    className="border-2 border-[#FF8C00] text-[#FF8C00] px-4 py-3 text-sm font-bold uppercase tracking-widest transition-colors duration-150 hover:bg-[#FF8C00] hover:text-white disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    <WarningCircle size={18} weight="bold" /> Changes
                  </button>
                  <button
                    data-testid="btn-skip"
                    onClick={() => takeAction('skip', null)}
                    disabled={loading}
                    className="border-2 border-[#71717A] text-[#71717A] px-4 py-3 text-sm font-bold uppercase tracking-widest transition-colors duration-150 hover:bg-[#71717A] hover:text-white disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    <SkipForward size={18} weight="bold" /> Skip
                  </button>
                </div>
              )}

              {isDone && (
                <div className="px-6 py-8 text-center" data-testid="episode-complete">
                  <h3 className="text-2xl font-black tracking-tighter font-[Chivo] uppercase">Episode Complete</h3>
                  <p className="text-sm text-[#52525B] mt-2">Total reward: <span className="font-mono font-bold">{totalReward.toFixed(4)}</span></p>
                  <button
                    data-testid="btn-restart"
                    onClick={() => resetEnv(selectedTask)}
                    className="mt-4 border-2 border-black bg-black text-white px-8 py-3 text-sm font-bold uppercase tracking-widest hover:bg-black/80 transition-colors duration-150"
                  >
                    Run Again
                  </button>
                </div>
              )}
            </>
          ) : (
            <div className="flex items-center justify-center flex-1 text-[#A1A1AA]">
              <p className="text-sm">Select a query to begin review</p>
            </div>
          )}
        </div>

        {/* Right: Stats & History */}
        <div className="col-span-3 flex flex-col overflow-y-auto" data-testid="sidebar">
          {/* Reward Panel */}
          <div className="p-6 border-b border-[#E4E4E7]">
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#A1A1AA] mb-3 block">Reward</span>
            <div className="flex gap-6">
              <Metric label="Total" value={totalReward.toFixed(2)} />
              {lastReward !== null && (
                <Metric
                  label="Last Step"
                  value={lastReward >= 0 ? `+${lastReward.toFixed(2)}` : lastReward.toFixed(2)}
                  sub={lastReward > 0 ? 'positive' : lastReward < 0 ? 'penalty' : 'neutral'}
                />
              )}
            </div>
          </div>

          {/* Session Stats */}
          <div className="p-6 border-b border-[#E4E4E7]">
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#A1A1AA] mb-3 block">Session</span>
            <div className="grid grid-cols-3 gap-4">
              <Metric label="Correct" value={observation.session_stats?.correct || 0} />
              <Metric label="Wrong" value={observation.session_stats?.wrong || 0} />
              <Metric label="Skipped" value={observation.session_stats?.skipped || 0} />
            </div>
            {/* Progress Bar */}
            <div className="mt-4">
              <div className="flex justify-between text-xs text-[#A1A1AA] mb-1">
                <span>Progress</span>
                <span>{observation.reviewed_count}/{observation.reviewed_count + observation.pending_count}</span>
              </div>
              <div className="w-full h-2 bg-[#E4E4E7]">
                <div
                  className="h-full bg-black transition-all duration-300"
                  style={{ width: `${((observation.reviewed_count) / Math.max(1, observation.reviewed_count + observation.pending_count)) * 100}%` }}
                />
              </div>
            </div>
          </div>

          {/* Action Result */}
          <div className="p-6 border-b border-[#E4E4E7]">
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#A1A1AA] mb-2 block">Last Action</span>
            <p className="font-mono text-xs text-[#52525B] break-all" data-testid="last-action-result">
              {observation.last_action_result}
            </p>
          </div>

          {/* Step History */}
          <div className="flex-1 flex flex-col min-h-0">
            <div className="p-4 border-b border-[#E4E4E7] flex items-center gap-2">
              <ChartBar size={16} />
              <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#A1A1AA]">History</span>
            </div>
            <div className="flex-1 overflow-y-auto" data-testid="step-history">
              {history.length === 0 ? (
                <div className="p-4 text-xs text-[#A1A1AA] text-center">No actions yet</div>
              ) : (
                history.map((h, i) => (
                  <div key={i} className="px-4 py-2.5 border-b border-[#E4E4E7] text-xs" data-testid={`history-step-${h.step}`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[#A1A1AA]">#{h.step}</span>
                        <span className="font-mono font-bold">{h.queryId}</span>
                      </div>
                      <span className={`font-mono font-bold ${h.reward > 0 ? 'text-[#00C853]' : h.reward < 0 ? 'text-[#FF2A00]' : 'text-[#A1A1AA]'}`}>
                        {h.reward >= 0 ? '+' : ''}{h.reward.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge color={h.verdict === 'approve' ? 'approve' : h.verdict === 'reject' ? 'reject' : 'skip'}>
                        {h.action}
                      </Badge>
                      {h.issues && h.issues.filter(i => i !== 'no_issues').map(issue => (
                        <span key={issue} className="text-[10px] text-[#52525B] uppercase">{issue.replace('_', ' ')}</span>
                      ))}
                    </div>
                  </div>
                ))
              )}
              <div ref={historyEndRef} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
