import React from "react";
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Unstable_Grid2';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';

function AnswerDetailsDialog(props) {

    const { answer, question, handleClose, open, runningTraces } = props;
    const [fullWidth, setFullWidth] = React.useState(true);
    const [maxWidth, setMaxWidth] = React.useState('xl');
    
    function removeCharFromStartAndEnd(str, charToRemove) {
        // Check if the string starts with the character
        while (str.startsWith(charToRemove)) {
          str = str.substring(1);
        }
        // Check if the string ends with the character
        while (str.endsWith(charToRemove)) {
          str = str.substring(0, str.length - 1);
        }
        return str;
    }

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
                    <Grid sm={12} md={6} lg={6}>
                    <Box sx={{ pt:2, pb:2 }}>
                            <Typography color="primary" variant="subtitle1" sx={{ fontWeight: "bold" }} gutterBottom>Question</Typography>
                            {question}
                        </Box>
                        <Box sx={{ pb: 2 }}>
                            <Typography color="primary" variant="subtitle1" sx={{ fontWeight: "bold" }} gutterBottom>Answer</Typography>
                            { answer.text.split("\n").map(function(item, idx) {
                                return (
                                    <span key={idx}>
                                        {item}
                                        <br/>
                                    </span>
                                )
                            }) }
                        </Box>
                    </Grid>
                    <Grid sm={12} md={6} lg={6} >
                        <Box sx={{ borderRadius: 4, pl:2, pr:2, pt:2,
                            background: "#B2DFDB"
                            }} >
                            <Box>
                                {runningTraces.map((row,index) => (
                                    Object.entries(row.trace).map((t,k) => (
                                        <div key={"trace-item"+k}>
                                            { Object.entries(t[1]).map((l,m) => (
                                                <Box key={"trace"+m}>
                                                    { l[0]==='rationale' && (
                                                        <Box sx={{ pb:2 }}>
                                                        <Typography variant="subtitle1" sx={{ fontWeight: "bold" }} gutterBottom>SQL Rationale</Typography>
                                                        { removeCharFromStartAndEnd(t[1]["rationale"]["text"], '\n') }
                                                        </Box>
                                                    )}

                                                    { l[0]==='invocationInput' && (
                                                        <Box sx={{ pb:2 }}>
                                                        <Typography variant="subtitle1" sx={{ fontWeight: "bold" }} gutterBottom>SQL Generated</Typography>
                                                        {
                                                        removeCharFromStartAndEnd(t[1]["invocationInput"]["actionGroupInvocationInput"]["requestBody"]["content"]["application/json"][0]["value"], '\n').split("\n").map(function(item, idx) {
                                                                return (
                                                                    <span key={idx}>
                                                                        {item}
                                                                        <br/>
                                                                    </span>
                                                                )
                                                            })
                                                        }
                                                        </Box>
                                                    )}
                                                </Box> 
                                            ))}
                                        </div>
                                    ))
                                ))}
                            </Box>
                        </Box>
                    </Grid>
                </Grid>
            </DialogContent>
            <DialogActions>
            <Button onClick={handleClose}>Close</Button>
            </DialogActions>
        </Dialog>
    );
}

export default AnswerDetailsDialog;