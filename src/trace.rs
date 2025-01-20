use serde::Serialize;
use std::sync::{LockResult, Mutex, MutexGuard};

/// A trace of a function call.
///
/// Includes the function name, the time the function was entered, the time the function was exited,
/// the arguments passed to the function, and the return value of the function.
#[derive(Debug, Clone, Serialize)]
pub struct FunctionEntryTrace {
    /// The time when the function was entered.
    pub timestamp: f64,

    /// The name of the function.
    pub function_name: String,

    /// The arguments passed to the function.
    pub args: Vec<(String, String)>,
}

#[derive(Debug, Clone, Serialize)]
pub struct FunctionExitTrace {
    /// The time when the function was exited.
    pub timestamp: f64,

    /// The name of the function.
    pub function_name: String,

    /// The return value of the function.
    pub return_value: Option<String>,
}

/// A trace of a branch condition.
#[derive(Debug, Clone, Serialize)]
pub struct BranchTrace {
    /// The time when the branch was evaluated.
    pub timestamp: f64,

    /// The name of the function where the branch code is located.
    pub function_name: Option<String>,

    /// The type of the branch.
    pub branch_type: String,

    /// The actual condition expression (e.g., "x > 0").
    pub condition_expr: String,

    /// List of (variable_name, value) pairs used in condition.
    pub evaluated_values: Vec<(String, String)>,

    /// Whether the condition was true or false.
    pub condition_result: bool,
}

#[derive(Debug, Clone, Serialize)]
pub struct AwaitTrace {
    /// The time when the await expression was evaluated.
    pub timestamp: f64,

    /// The name of the function where the await expression is located.
    pub function_name: String,

    /// The expression being awaited.
    pub await_expr: String,

    /// The value being awaited.
    pub await_value: String,

    /// The result of the await.
    pub await_result: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct YieldTrace {
    /// The time when the yield expression was evaluated.
    pub timestamp: f64,

    /// The name of the function where the yield expression is located.
    pub function_name: String,

    /// The value being yielded from the generator.
    pub yield_value: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct YieldResumeTrace {
    /// The time when the yield expression was evaluated.
    pub timestamp: f64,

    /// The name of the function where the yield expression is located.
    pub function_name: String,

    /// The value being sent back to the generator.
    pub send_value: String,
}

/// A trace of a function call or a branch condition.
#[derive(Debug, Clone, Serialize)]
#[serde(tag = "type")]
pub enum Trace {
    FunctionEntry(FunctionEntryTrace),
    FunctionExit(FunctionExitTrace),
    Branch(BranchTrace),
    Await(AwaitTrace),
    Yield(YieldTrace),
    YieldResume(YieldResumeTrace),
}

impl std::fmt::Display for Trace {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Trace::FunctionEntry(trace) => write!(f, "{:?}", trace),
            Trace::FunctionExit(trace) => write!(f, "{:?}", trace),
            Trace::Branch(trace) => write!(f, "{:?}", trace),
            Trace::Await(trace) => write!(f, "{:?}", trace),
            Trace::Yield(trace) => write!(f, "{:?}", trace),
            Trace::YieldResume(trace) => write!(f, "{:?}", trace),
        }
    }
}

impl From<FunctionEntryTrace> for Trace {
    fn from(trace: FunctionEntryTrace) -> Self {
        Self::FunctionEntry(trace)
    }
}

impl From<FunctionExitTrace> for Trace {
    fn from(trace: FunctionExitTrace) -> Self {
        Self::FunctionExit(trace)
    }
}

impl From<BranchTrace> for Trace {
    fn from(trace: BranchTrace) -> Self {
        Self::Branch(trace)
    }
}

impl From<AwaitTrace> for Trace {
    fn from(trace: AwaitTrace) -> Self {
        Self::Await(trace)
    }
}

impl From<YieldTrace> for Trace {
    fn from(trace: YieldTrace) -> Self {
        Self::Yield(trace)
    }
}

impl From<YieldResumeTrace> for Trace {
    fn from(trace: YieldResumeTrace) -> Self {
        Self::YieldResume(trace)
    }
}

/// A collector of traces.
#[derive(Debug)]
pub struct TraceCollector {
    traces: Mutex<Vec<Trace>>,
}

#[allow(unused)]
impl TraceCollector {
    pub fn new() -> Self {
        Self {
            traces: Mutex::new(Vec::new()),
        }
    }

    pub fn add_trace(&self, trace: Trace) {
        self.traces.lock().unwrap().push(trace);
    }

    pub fn traces_mut(&self) -> LockResult<MutexGuard<Vec<Trace>>> {
        self.traces.lock()
    }

    pub fn to_vec(&self) -> Vec<Trace> {
        self.traces.lock().unwrap().clone()
    }

    pub fn to_json(&self) -> String {
        serde_json::to_string(&self.to_vec()).unwrap()
    }
}
