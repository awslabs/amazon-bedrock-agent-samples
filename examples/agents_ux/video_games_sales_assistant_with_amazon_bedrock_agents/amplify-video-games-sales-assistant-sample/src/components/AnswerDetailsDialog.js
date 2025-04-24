import React from "react";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import Grid from "@mui/material/Grid";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import OrchestrationRationaleTraceViewer from "./OrchestrationRationaleTraceViewer.js";
import MarkdownRenderer from "./MarkdownRenderer.js";

const AnswerDetailsDialog = ({ answer, question, handleClose, open }) => {
  const [fullWidth, setFullWidth] = React.useState(true);
  const [maxWidth, setMaxWidth] = React.useState("xxl");

  return (
    <Dialog
      fullWidth={fullWidth}
      maxWidth={maxWidth}
      open={open}
      onClose={handleClose}
    >
      <DialogTitle>Answer Details</DialogTitle>
      <DialogContent>
        <Grid container rowSpacing={1} columnSpacing={{ xs: 1, sm: 2, md: 3 }}>
          <Grid size={{ sm: 12, md: 12, xs: 6, md: 6 }}>
            <Box key="question_value" sx={{ pt: 2, pb: 2 }}>
              <Typography
                color="primary"
                variant="subtitle1"
                sx={{ fontWeight: "bold" }}
                gutterBottom
              >
                Question
              </Typography>
              {question}
            </Box>
            <Box key="answer_value">
              <Typography
                component="div"
                color="primary"
                variant="subtitle1"
                sx={{ fontWeight: "bold" }}
                gutterBottom
              >
                Answer
              </Typography>
              <Typography component="div" variant="body1">
                <MarkdownRenderer content={answer.text} />
              </Typography>
            </Box>
          </Grid>
          <Grid size={{ sm: 12, md: 12, xs: 6, md: 6 }}>
            <Box
              sx={{
                borderRadius: 4,
                p: 2,
                background: "#A4E9DB",
              }}
            >
              <OrchestrationRationaleTraceViewer
                traces={answer.runningTraces}
              />
            </Box>
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default AnswerDetailsDialog;
