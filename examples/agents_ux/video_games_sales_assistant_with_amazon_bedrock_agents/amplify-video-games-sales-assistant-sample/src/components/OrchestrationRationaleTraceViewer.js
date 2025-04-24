import React from "react";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./OrchestrationRationaleTraceViewer.css";

const OrchestrationRationaleTraceViewer = ({ traces }) => {
  // Extract all rationale and query information from traces in order of appearance
  const traceItems = [];

  traces.forEach((trace) => {
    if (trace.orchestrationTrace) {
      // Track rationales
      if (trace.orchestrationTrace.rationale) {
        const rationaleText = trace.orchestrationTrace.rationale.text;
        traceItems.push({
          type: "rationale",
          text: rationaleText,
        });
      }
      // Track queries from invocationInput
      if (
        trace.orchestrationTrace.invocationInput &&
        trace.orchestrationTrace.invocationInput.actionGroupInvocationInput &&
        trace.orchestrationTrace.invocationInput.actionGroupInvocationInput
          .requestBody &&
        trace.orchestrationTrace.invocationInput.actionGroupInvocationInput
          .requestBody.content
      ) {
        const content =
          trace.orchestrationTrace.invocationInput.actionGroupInvocationInput
            .requestBody.content;

        if (content["application/json"]) {
          const sqlQueryParam = content["application/json"].find(
            (param) => param.name === "SQLQuery"
          );
          if (sqlQueryParam) {
            traceItems.push({
              type: "query",
              text: sqlQueryParam.value,
            });
          }
        }
      }
    }
  });

  return (
    <Box>
      {traceItems.length > 0 ? (
        traceItems.map((item, index) => (
          <Box key={index} className="trace-item">
            {item.type === "rationale" && (
              <Box className="rationale-section">
                <Typography
                  variant="subtitle1"
                  sx={{ fontWeight: "bold" }}
                  gutterBottom
                >
                  SQL Rationale
                </Typography>
                <ReactMarkdown
                  remarkPlugins={[[remarkGfm, { singleTilde: false }]]}
                >
                  {item.text}
                </ReactMarkdown>
              </Box>
            )}

            {item.type === "query" && (
              <Box className="query-section">
                <Typography
                  component="div"
                  variant="subtitle1"
                  sx={{ fontWeight: "bold" }}
                  gutterBottom
                >
                  SQL Generated
                </Typography>
                <pre>{item.text}</pre>
              </Box>
            )}
          </Box>
        ))
      ) : (
        <p>No rationale or queries found in the traces.</p>
      )}
    </Box>
  );
};

export default OrchestrationRationaleTraceViewer;
