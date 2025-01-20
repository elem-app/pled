class GraphGenerator {
  constructor(data) {
    this.data = data;
    this.initializeMermaid();
  }

  initializeMermaid() {
    mermaid.initialize({
      startOnLoad: true,
      theme: "default",
      fontFamily: "Courier New, monospace",
    });
  }

  generateMermaidDefinition() {
    const diagram = ["sequenceDiagram", "    create actor pled"];
    const stack = ["pled"];
    const used = new Map();
    for (const trace of this.data) {
      let displayName,
        participant,
        caller = null;
      if (trace.function_name) {
        const lastDotIndex = trace.function_name.lastIndexOf(".");
        if (lastDotIndex === -1) {
          displayName = trace.function_name;
          participant = trace.function_name;
        } else {
          const moduleName = trace.function_name.slice(0, lastDotIndex);
          const functionName = trace.function_name.slice(lastDotIndex + 1);
          displayName = `${moduleName}<br>${functionName}`;
          participant = trace.function_name.replace(".", "__");
        }
        if (used.has(displayName)) {
          participant = `${participant}__${used.get(displayName)}`;
        }
      } else {
        displayName = null;
        participant = stack[stack.length - 1];
      }
      switch (trace.type) {
        case "FunctionEntry":
          caller = stack[stack.length - 1];
          const formattedArgs = trace.args.map(([name, value]) => `${name}=${value}`).join(", ");
          diagram.push(
            `    create participant ${participant} as ${displayName}`
          );
          diagram.push(`    ${caller}->>${participant}: ${formattedArgs}`);
          stack.push(participant);
          break;
        case "FunctionExit":
          stack.pop();
          caller = stack[stack.length - 1];
          diagram.push(`    destroy ${participant}`);
          diagram.push(
            `    ${participant}->>${caller}: return ${trace.return_value}`
          );
          if (used.has(displayName)) {
            used.set(displayName, used.get(displayName) + 1);
          } else {
            used.set(displayName, 1);
          }
          break;
        case "Branch":
          diagram.push(
            `    ${participant}-->${participant}: ${trace.branch_type} ${trace.condition_expr}<br>=> ${trace.condition_result}`
          );
          break;
        case "Await":
          diagram.push(
            `    ${participant}-->${participant}: ${trace.await_expr}<br>=> ${trace.await_result}`
          );
          break;
        case "Yield":
          stack.pop();
          caller = stack[stack.length - 1];
          diagram.push(
            `    ${participant}-->>+${caller}: yield ${trace.yield_value}`
          );
          break;
        case "YieldResume":
          caller = stack[stack.length - 1];
          diagram.push(`    ${caller}-->>-${participant}: send ${trace.send_value}`);
          stack.push(participant);
          break;
      }
    }
    return diagram.join("\n");
  }

  render() {
    const root = document.getElementById("root");

    // Create container
    const container = document.createElement("div");
    container.className = "graph-container";

    // Add diagram
    const diagram = document.createElement("div");
    diagram.className = "mermaid";
    diagram.textContent = this.generateMermaidDefinition();
    container.appendChild(diagram);

    // Add controls
    const controls = this.createControls();
    container.appendChild(controls);

    root.appendChild(container);
    mermaid.contentLoaded();
  }

  createControls() {
    const controls = document.createElement("div");
    controls.className = "controls";

    // // Add search, filters, etc.
    // const search = document.createElement("input");
    // search.type = "text";
    // search.placeholder = "Search relationships...";
    // search.addEventListener("input", this.handleSearch.bind(this));

    // controls.appendChild(search);
    return controls;
  }

  handleSearch(event) {
    const searchTerm = event.target.value.toLowerCase();
    // Implement filtering logic
  }
}

// Initialize when document loads
document.addEventListener("DOMContentLoaded", () => {
  const generator = new GraphGenerator(traceData);
  generator.render();
});
