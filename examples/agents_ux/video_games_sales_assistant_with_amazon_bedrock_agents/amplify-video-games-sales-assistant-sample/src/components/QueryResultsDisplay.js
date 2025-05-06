import React from "react";
import { Box, Typography } from "@mui/material";
import TableView from "./TableView";

const QueryResultsDisplay = ({ index, answer }) => {
  return (
    <Box>
      {answer.queryResults.map((query_result, x) => (
        <Box key={"table_" + index + "_" + x}>
          {query_result.query_results.length > 0 ? (
            <TableView query_results={query_result.query_results} />
          ) : (
            <Typography sx={{ textAlign: "center" }}>
              No Data Records
            </Typography>
          )}
          <Typography
            component="div"
            variant="body1"
            sx={{
              fontSize: "0.85rem",
              pl: 2,
              pr: 2,
              pt: 1,
              pb: 1,
              m: 0,
              background: "#efefef",
              borderBottomRightRadius: 16,
              borderBottomLeftRadius: 16,
              mb: x === answer.queryResults.length - 1 ? 1 : 4,
              boxShadow: "rgba(0, 0, 0, 0.05) 0px 4px 12px",
            }}
          >
            <strong>Query:</strong> {query_result.query}
          </Typography>
        </Box>
      ))}
    </Box>
  );
};

export default QueryResultsDisplay;
