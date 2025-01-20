use crate::trace::{
    AwaitTrace, BranchTrace, FunctionEntryTrace, FunctionExitTrace, TraceCollector,
    YieldResumeTrace, YieldTrace,
};
use pyo3::prelude::*;
use std::{fs, sync::Arc, time::Instant};

#[pyclass]
#[pyo3(name = "Tracer")]
pub struct PyTracer {
    collector: Arc<TraceCollector>,
    start_instant: Instant,
}

impl PyTracer {
    fn timestamp(&self) -> f64 {
        self.start_instant.elapsed().as_secs_f64()
    }
}

#[pymethods]
impl PyTracer {
    #[new]
    fn new() -> Self {
        Self {
            collector: Arc::new(TraceCollector::new()),
            start_instant: Instant::now(),
        }
    }

    #[pyo3(signature = (function_name, args))]
    fn trace_fentry(&self, function_name: String, args: Vec<(String, String)>) -> PyResult<()> {
        self.collector.add_trace(
            FunctionEntryTrace {
                timestamp: self.timestamp(),
                function_name,
                args,
            }
            .into(),
        );
        Ok(())
    }

    #[pyo3(signature = (function_name, return_value=None))]
    fn trace_fexit(&self, function_name: String, return_value: Option<String>) -> PyResult<()> {
        self.collector.add_trace(
            FunctionExitTrace {
                timestamp: self.timestamp(),
                function_name,
                return_value,
            }
            .into(),
        );
        Ok(())
    }

    #[pyo3(signature = (function_name, branch_type, condition_expr, evaluated_values, condition_result))]
    fn trace_branch(
        &self,
        function_name: Option<String>,
        branch_type: String,
        condition_expr: String,
        evaluated_values: Vec<(String, String)>,
        condition_result: bool,
    ) -> PyResult<()> {
        self.collector.add_trace(
            BranchTrace {
                timestamp: self.timestamp(),
                function_name,
                branch_type,
                condition_expr,
                evaluated_values,
                condition_result,
            }
            .into(),
        );
        Ok(())
    }

    #[pyo3(signature = (function_name, await_expr, await_value, await_result))]
    fn trace_await(
        &self,
        function_name: String,
        await_expr: String,
        await_value: String,
        await_result: String,
    ) -> PyResult<()> {
        self.collector.add_trace(
            AwaitTrace {
                timestamp: self.timestamp(),
                function_name,
                await_expr,
                await_value,
                await_result,
            }
            .into(),
        );

        Ok(())
    }

    #[pyo3(signature = (function_name, yield_value))]
    fn trace_yield(&self, function_name: String, yield_value: String) -> PyResult<()> {
        self.collector.add_trace(
            YieldTrace {
                timestamp: self.timestamp(),
                function_name,
                yield_value,
            }
            .into(),
        );
        Ok(())
    }

    #[pyo3(signature = (function_name, send_value))]
    fn trace_yield_resume(&self, function_name: String, send_value: String) -> PyResult<()> {
        self.collector.add_trace(
            YieldResumeTrace {
                timestamp: self.timestamp(),
                function_name,
                send_value,
            }
            .into(),
        );
        Ok(())
    }

    fn format_traces(&self) -> PyResult<String> {
        let traces = self.collector.to_vec();
        Ok(traces
            .iter()
            .enumerate()
            .map(|(i, trace)| format!("{:3}: {}", i + 1, trace))
            .collect::<Vec<_>>()
            .join("\n"))
    }

    fn dump_json(&self) -> PyResult<String> {
        Ok(self.collector.to_json())
    }

    #[pyo3(signature = (path))]
    fn dump_report_file(&self, path: &str) -> PyResult<()> {
        let json_data = self.collector.to_json();
        let html_data = format!(
            r#"<!DOCTYPE html>
<html><head><script type="module">import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11.4.1/+esm'
const traceData = {};{}</script></head><body><div id="root"></div></body></html>"#,
            json_data,
            include_str!("../assets/generator.js")
        );

        fs::write(path, html_data.as_bytes())?;

        Ok(())
    }
}
