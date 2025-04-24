import React from "react";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";

function TableView(props) {
  const { query_results } = props;

  return (
    <TableContainer sx={{ border: 0, width: "100%" }}>
      <Table
        sx={{
          border: 0,
          boxShadow: "rgba(0, 0, 0, 0.05) 0px 4px 12px",
          borderTopRightRadius: 16,
          borderTopLeftRadius: 16,
          width: "100%",
        }}
        aria-label="simple table"
      >
        <TableHead>
          <TableRow>
            <TableCell></TableCell>
            {Object.entries(query_results[0]).map((t, k) => (
              <TableCell
                key={"row_cell_head_" + k}
                sx={{ p: 1, pr: 2 }}
                align={typeof t[1] == "number" ? "right" : "left"}
              >
                {t[0]}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>

        <TableBody>
          {query_results.map((row, x) => (
            <TableRow
              key={"row" + x}
              sx={{ "&:last-child td, &:last-child th": { border: 0 } }}
            >
              <TableCell sx={{ p: 1, m: 0 }} align="right">
                {x + 1}
              </TableCell>
              {Object.entries(row).map((t, k) => (
                <TableCell
                  key={"row_cell_" + x + "_" + k}
                  sx={{ p: 1, pr: 2, m: 0 }}
                  component={k === 0 ? "th" : ""}
                  scope={k === 0 ? "row" : ""}
                  align={typeof t[1] === "number" ? "right" : "left"}
                >
                  {t[1]}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

export default TableView;
