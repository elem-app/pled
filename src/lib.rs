use pyo3::{
    pymodule,
    types::{PyModule, PyModuleMethods},
    Bound, PyResult,
};

mod pytracer;
mod trace;

#[pymodule]
#[pyo3(name = "_pled")]
fn _pled(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<pytracer::PyTracer>()?;

    Ok(())
}
