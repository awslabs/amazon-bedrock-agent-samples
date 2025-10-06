import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import IconButton from "@mui/material/IconButton";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { alpha } from "@mui/material/styles";
import MarkdownRenderer from "./MarkdownRenderer.js";

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
          <Box key={index} sx={{ mb: 2 }}>
            {item.type === "rationale" && (
              <Box sx={{ mb: 2 }}>
                <Typography
                  variant="subtitle1"
                  color="primary"
                  sx={{ fontWeight: "bold" }}
                  gutterBottom
                >
                  SQL Rationale
                </Typography>
                <MarkdownRenderer content={item.text} />
              </Box>
            )}

            {item.type === "query" && (
              <Box sx={{ mb: 2 }}>
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  <Typography
                    component="div"
                    variant="subtitle1"
                    color="secondary"
                    sx={{ fontWeight: "bold" }}
                  >
                    SQL Generated
                  </Typography>
                  <IconButton
                    size="small"
                    onClick={() => navigator.clipboard.writeText(item.text)}
                    sx={{ color: "secondary.main" }}
                  >
                    <ContentCopyIcon fontSize="small" />
                  </IconButton>
                </Box>
                <Box
                  component="pre"
                  sx={(theme) => ({
                    backgroundColor: "rgba(0, 0, 0, 0.02)",
                    border: `1px solid ${alpha(
                      theme.palette.secondary.main,
                      0.3
                    )}`,
                    borderRadius: 2,
                    padding: theme.spacing(1.5),
                    fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                    fontSize: "0.875rem",
                    overflow: "auto",
                    margin: 0,
                  })}
                >
                  {item.text}
                </Box>
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
