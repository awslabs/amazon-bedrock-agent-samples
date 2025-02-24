import React, { useLayoutEffect, useRef, useEffect } from "react";
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import SendIcon from '@mui/icons-material/Send';
import Paper from '@mui/material/Paper';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Unstable_Grid2';
import InputBase from '@mui/material/InputBase';
import Divider from '@mui/material/Divider';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import Button from '@mui/material/Button';
import Grow from '@mui/material/Grow';
import Stack from '@mui/material/Stack';
import Fade from '@mui/material/Fade';
import { v4 as uuidv4 } from 'uuid';
import { BedrockAgentRuntimeClient, InvokeAgentCommand, BedrockAgentRuntimeClientConfigType } from "@aws-sdk/client-bedrock-agent-runtime";
import { BedrockRuntimeClient, InvokeModelCommand } from "@aws-sdk/client-bedrock-runtime";
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, QueryCommand } from "@aws-sdk/lib-dynamodb";
import { fromCognitoIdentityPool } from "@aws-sdk/credential-providers";

import InsightsOutlinedIcon from '@mui/icons-material/InsightsOutlined';
import QuestionAnswerOutlinedIcon from '@mui/icons-material/QuestionAnswerOutlined';
import PsychologyRoundedIcon from '@mui/icons-material/PsychologyRounded';
import TableRowsRoundedIcon from '@mui/icons-material/TableRowsRounded';

import AnswerDetailsDialog from './AnswerDetailsDialog.js';
import { WELCOME_MESSAGE, MAX_LENGTH_INPUT_SEARCH, AGENT_ID, AGENT_ALIAS_ID, QUESTION_ANSWERS_TABLE_NAME, CHART_PROMPT, MODEL_ID_FOR_CHART_AND_DASHBOARD, ACCESS_KEY_ID, SECRET_ACCESS_KEY, AWS_REGION } from '../env';
import TableView from './TableView.js';
import MyChart from './MyChart.js';

const Chat = ({}) => {
    
    const [totalAnswers, setTotalAnswers] = React.useState(0);
    const [enabled,setEnabled] = React.useState(false);
    const [loading,setLoading] = React.useState(false);
    const [controlAnswers,setControlAnswers] = React.useState([]);
    const [answers,setAnswers] = React.useState([]);
    const [query,setQuery] = React.useState("");
    const [sessionId,setSessionId] = React.useState(uuidv4());
    const [errorMessage,setErrorMessage] = React.useState("");
    const [height,setHeight] = React.useState(480);
    const [openAnswerDetails, setOpenAnswerDetails] = React.useState(false);
    const [size, setSize] = React.useState([0, 0]);
    const [selectedAB, setSelectedAB] = React.useState(0);
    const [selectedB, setSelectedB] = React.useState(0);

    const scrollRef = useRef(null);
    useEffect(() => {
        if (scrollRef.current) {
          scrollRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [answers]);

    useLayoutEffect(() => {
        function updateSize() {
            setSize([window.innerWidth, window.innerHeight]);
            const myh = window.innerHeight-172;
            if (myh<346){
                setHeight(346)
            }else{
                setHeight(myh)
            }
        }
        window.addEventListener('resize', updateSize);
        updateSize();
        return () => window.removeEventListener('resize', updateSize);
    }, []);

    const effectRan = React.useRef(false);
    useEffect(() => {
      if (!effectRan.current) {
        console.log("effect applied - only on the FIRST mount");
        const fetchData = async () => {
            console.log("Chat")
        }
        fetchData()
            // catch any error
            .catch(console.error);
      }
      return () => effectRan.current = true;
    }, []);

    const handleQuery = (event) => {
        if (event.target.value.length>0 && loading===false && query!=="")
            setEnabled(true)
        else
            setEnabled(false)
        setQuery(event.target.value.replace("\n",""))
    }

    const handleKeyPress = (event) => {
        if (event.code === "Enter" && loading===false && query!==""){
            getAnswer(query);
        }
    }

    const handleClick = async (e) => {
        e.preventDefault();
        if (query!==""){
            getAnswer(query);
        }
    }

    function extractBetweenTags(string, tag) {
        const startTag = `<${tag}>`;
        const endTag = `</${tag}>`;
        const startIndex = string.indexOf(startTag) + startTag.length;
        const endIndex = string.indexOf(endTag, startIndex);
        if (startIndex === -1 || endIndex === -1) {
          return '';
        }
        return string.slice(startIndex, endIndex);
    }

    function removeCharFromStartAndEnd(str, charToRemove) {
        while (str.startsWith(charToRemove)) {
          str = str.substring(1);
        }
        while (str.endsWith(charToRemove)) {
          str = str.substring(0, str.length - 1);
        }
        return str;
    }
    
    const getAnswer = async (my_query) => {

        if (!loading && my_query!==""){
            setControlAnswers(prevState => [...prevState, { }]);
            setAnswers(prevState => [...prevState, { query: my_query }]);
            setEnabled(false)
            setLoading(true)
            setErrorMessage("")
            setQuery("");
            try {
                const { completion, usage, totalInputTokens, totalOutputTokens, runningTraces, queryUuid } = await invokeBedrockAgent(my_query, sessionId)
                console.log("------- completion -------");
                console.log(completion);
                console.log("------- running traces -------");
                console.log(runningTraces);
                let json = {
                    text: completion,
                    usage,
                    totalInputTokens,
                    totalOutputTokens,
                    runningTraces,
                    queryUuid
                }
                const queryResults = await getQueryResults(json);
                if (queryResults.length>0) {
                    json.chart = "loading";
                    json.queryResults = queryResults;
                }
                setLoading(false);
                setEnabled(false);
                setControlAnswers(prevState => [...prevState, { current_tab_view: 'answer' }]);
                setAnswers(prevState => [...prevState, json ]);
                if (queryResults.length>0) {
                    json.chart = await generateChart(json, queryResults);
                    console.log("------- answer with chart-------");
                    console.log(json);
                }else{
                    console.log("------- answer without chart-------");
                    console.log(json);
                }
                setTotalAnswers(prevState => prevState + 1)
            } catch (error) {
                console.log('Call failed: ', error);
                setErrorMessage(error.toString());
                setLoading(false)
                setEnabled(false)
            }
        }
    }

    const invokeBedrockAgent = async (prompt, sessionId) => {

        const bedrock = new BedrockAgentRuntimeClient({
            region: AWS_REGION,
            credentials: {
                accessKeyId: ACCESS_KEY_ID,
                secretAccessKey: SECRET_ACCESS_KEY
            },
        });
        
        const now = new Date();
        const formattedDate = now.toLocaleString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
        const formattedTime = now.toLocaleString('en-US', { timeStyle: 'short' });
        const queryUuid = uuidv4()
        const input = {
            agentId: AGENT_ID,
            agentAliasId: AGENT_ALIAS_ID,
            sessionId,
            inputText: prompt,
            sessionState: {
                promptSessionAttributes: {
                    currentDate: formattedDate,
                    currentTime: formattedTime,
                    queryUuid: queryUuid
                }
            },
            enableTrace: true
        };
        console.log("------- invokeAgent -------");
        console.log(input)
        const command = new InvokeAgentCommand(input);
        let completion = "";
        let runningTraces = [];
        const response = await bedrock.send(command);
        if (response.completion === undefined) {
            throw new Error("Completion is undefined");
        }
        for await (let chunkEvent of response.completion) {
            if (chunkEvent.chunk) {
                const chunk = chunkEvent.chunk;
                //console.log(chunk);
                const decodedResponse = new TextDecoder("utf-8").decode(chunk.bytes);
                completion += decodedResponse;
            }
            if (chunkEvent.trace) {
                runningTraces = [...runningTraces, chunkEvent.trace];
            }
        }
        return { completion, runningTraces, queryUuid };  
    };

    const getQueryResults = async (answer) => {
        let queryResults = [];
        try {
            const client = new DynamoDBClient({
                region: AWS_REGION,
                credentials: {
                    accessKeyId: ACCESS_KEY_ID,
                    secretAccessKey: SECRET_ACCESS_KEY
                },
            });
            const docClient = DynamoDBDocumentClient.from(client);
            
            const params = {
                TableName: QUESTION_ANSWERS_TABLE_NAME,
                //IndexName: "GSI1",
                KeyConditionExpression: "#id = :queryUuid AND #my_timestamp > :minValue",
                ExpressionAttributeNames: {
                  "#id": "id",
                  "#my_timestamp": "my_timestamp",
                },
                ExpressionAttributeValues: {
                  ":queryUuid": answer.queryUuid,
                  ":minValue": 0,
                },
            };
            console.log("------- get data source -------");
            console.log(params);
            const command = new QueryCommand(params);
            const response = await docClient.send(command);
            console.log(response);
            if (response.hasOwnProperty("Items")){
                for (let i = 0; i < response.Items.length; i++) {
                    queryResults.push({ "query": response.Items[i].query, "query_results": JSON.parse(response.Items[i].data).result })
                }
            }
            console.log("------- data uuid -------");
            console.log(response)
            return queryResults
        }catch (error) {
            console.log('Call failed: ', error);
            return queryResults
        }
    }

    const handleFormatter = (obj) => {
        if (typeof obj === 'object' && obj !== null) {
          for (let key in obj) {
            if (typeof obj[key] === 'string') {
              if (key==="formatter" &&  (obj[key]==="%" || obj[key].startsWith("$") )){
                handleFormatter(obj[key]);
              // Convert the function string to an actual function
              }else if (key==="formatter"){
                obj[key] = new Function('return ' + obj[key])();
              }else{
                handleFormatter(obj[key]);
              }
            } else if (typeof obj[key] === 'object') {
              handleFormatter(obj[key]);
            }
          }
        }
        return obj;
    };

    const generateChart = async (answer, answerDetails) => {

        const bedrock = new BedrockRuntimeClient({
            region: AWS_REGION,
            credentials: {
                accessKeyId: ACCESS_KEY_ID,
                secretAccessKey: SECRET_ACCESS_KEY
            },
        });

        let query_results = ""
        for (let i = 0; i < answerDetails.length; i++) {
            query_results += JSON.stringify(answerDetails[i].query_results) + "\n"
        }

        let new_chart_prompt = CHART_PROMPT.replace(/<<answer>>/i, answer.text)
        new_chart_prompt = new_chart_prompt.replace(/<<data_sources>>/i, query_results)

        const payload = {
            anthropic_version: "bedrock-2023-05-31",
            max_tokens: 2000,
            temperature: 1,
            messages: [
              {
                role: "user",
                content: [{ type: "text", text: new_chart_prompt }],
              },
            ],
        };
        console.log("------- request chart -------");
        console.log(payload);
        const command = new InvokeModelCommand({
            contentType: "application/json",
            body: JSON.stringify(payload),
            modelId: MODEL_ID_FOR_CHART_AND_DASHBOARD
        });
        const apiResponse = await bedrock.send(command);
        // Decode and return the response(s)
        const decodedResponseBody = new TextDecoder().decode(apiResponse.body);
        /** @type {MessagesResponseBody} */
        const responseBody = JSON.parse(decodedResponseBody).content[0].text;
        console.log("------- response chart generation -------");
        console.log(responseBody);
        const has_chart = parseInt(extractBetweenTags(responseBody,'has_chart'))
        try {
            if (has_chart){
                const chart = {
                    chart_type : removeCharFromStartAndEnd(extractBetweenTags(responseBody,'chart_type'), '\n'),
                    chart_configuration : handleFormatter(JSON.parse(extractBetweenTags(responseBody,'chart_configuration'))),
                    caption : removeCharFromStartAndEnd(extractBetweenTags(responseBody,'caption'), '\n')
                }
                chart.chart_configuration.options.chart.zoom = { enabled: false }
                if (chart.chart_configuration.options.hasOwnProperty("title")){
                    chart.chart_configuration.options.title.align = "center"
                }
                if (chart.chart_configuration.options.hasOwnProperty("subtitle")){
                    chart.chart_configuration.options.subtitle.align = "center"
                }
                console.log("------- final chart generation -------");
                console.log(chart)
                return chart;
            }else{
                return {
                    rationale : removeCharFromStartAndEnd(extractBetweenTags(responseBody, 'rationale'), '\n')
                }
            }
        }catch (error) {
            console.log('Call failed: ', error);
            return {
                rationale : "Error parsing."
            }
        }
    };
    
    const handleCloseAnswerDetails = () => {
        setOpenAnswerDetails(false);
    };

    const handleClickOpenAnswerDetails = (value) => () => {
        setSelectedAB(value);
        setSelectedB(value);
        setOpenAnswerDetails(true);
    };

    const handleShowTab = (index, type) => () => {
        const updatedItems = [...controlAnswers];
        updatedItems[index] = { ...updatedItems[index], current_tab_view: type };
        setControlAnswers(updatedItems);
    };

    return (
    <Box sx={{ pl: 2, pr: 2, pt:0, pb:0 }}>

        { errorMessage!=="" && (
            <Alert severity="error" sx={{ 
                position: "fixed",
                width: "80%",
                top: "65px",
                left: "20%",
                marginLeft: "-10%"
            }} onClose={() => { setErrorMessage("") }}>
            {errorMessage}</Alert>
        )}

        <Box
        id="chatHelper"
        sx={{
            display: "flex",
            flexDirection: "column",
            height: height,
            overflow: "hidden",
            overflowY: "scroll",
            }}
        >
            { answers.length>0 ? (
            <ul style={{ paddingBottom: 14 }}>
            {answers.map((answer, index) => (
                <li key={"meg"+index}>
                    { answer.hasOwnProperty("text") ? (
                            <Box  sx={{ 
                                borderRadius: 4, 
                                pl: 1, pr: 1, pt: 1, 
                                display: 'flex',
                                alignItems: 'left'
                            }}>
                                <Box sx={{ pr: 1, pl:0.5 }}>
                                    <img src="/images/genai.png" alt="Amazon Bedrock" width={28} height={28} />
                                </Box>
                                <Box sx={{ p:0 }}>

                                    <Box>
                                        <Grow in={ (controlAnswers[index].current_tab_view==='answer') ? true : false  }>
                                            <Box id={"answer"+index} style={{ display: (controlAnswers[index].current_tab_view==='answer') ? "block" : "none" }} >
                                                <Typography variant="body1">
                                                {
                                                answer.text.split("\n").map(function(item, idx) {
                                                        return (
                                                            <span key={idx}>
                                                                {item}
                                                                <br/>
                                                            </span>
                                                        )
                                                    })
                                                }
                                                </Typography>
                                            </Box>
                                        </Grow>

                                        { ( answer.hasOwnProperty("queryResults") ) && (
                                            <Grow in={ (controlAnswers[index].current_tab_view==='records') ? true : false }>
                                                <Box style={{ display: (controlAnswers[index].current_tab_view==='records') ? "block" : "none" }} sx={{ pt:2 }} >
                                                    {answer.queryResults.map((query_result, x) => (
                                                        <Box key={"table_"+index+"_"+x}>
                                                            <TableView query_results={query_result.query_results}/>
                                                            <Typography component="div" variant="body1" sx={{ fontSize: "0.85rem", pl:2, pr: 2, pt:1, pb:1, m:0, background: "#efefef", borderBottomRightRadius: 16, borderBottomLeftRadius: 16, mb: (x===(answer.queryResults.length-1)) ? 1 : 4, boxShadow: 'rgba(0, 0, 0, 0.05) 0px 4px 12px' }} >
                                                                <strong>Query:</strong> { query_result.query }
                                                            </Typography>
                                                        </Box>
                                                    ))}

                                                </Box>
                                            </Grow>
                                        )}

                                        { ( answer.hasOwnProperty("chart") && answer.chart.hasOwnProperty("chart_type") ) && (
                                            <Grow in={ (controlAnswers[index].current_tab_view==='chart') ? true : false }>
                                                <Box style={{ display: (controlAnswers[index].current_tab_view==='chart') ? "block" : "none" }} >
                                                    <Typography variant="body1" sx={{ pb:2 }}>
                                                    {
                                                    answer.chart.caption.split("\n").map(function(item, idx) {
                                                            return (
                                                                <span key={idx}>
                                                                    {item}
                                                                    <br/>
                                                                </span>
                                                            )
                                                        })
                                                    }
                                                    </Typography>
                                                    <Box sx={(theme) => ({ background: "#FFF", pt:0, pb:2, pl:2, pr: 2, m:0, borderRadius: 4, 
                                                        boxShadow: 'rgba(0, 0, 0, 0.05) 0px 4px 12px',
                                                        bgcolor: 'rgba(248, 255, 252, 0.4)'
                                                        })}
                                                    >
                                                        <MyChart options={answer.chart.chart_configuration.options} series={answer.chart.chart_configuration.series} type={answer.chart.chart_type} />
                                                    </Box>
                                                </Box>
                                            </Grow>
                                        )}
                                    </Box>
                                    
                                    { answer.hasOwnProperty('chart') && (

                                    <Grid container spacing={2} sx={{ display: 'flex', alignItems: 'center' }}>
                                        <Grid>
                                            <IconButton 
                                                size="small"
                                                onClick={handleClickOpenAnswerDetails(index)}
                                                >
                                                    <PsychologyRoundedIcon fontSize="small" />
                                            </IconButton>
                                        </Grid>

                                        { answer.queryResults.length>0 && (
                                            <Grid>
                                                <Fade timeout={1000} in={ answer.queryResults.length>0 }>
                                                    <div>
                                                        <Button
                                                        disabled={ (controlAnswers[index].current_tab_view==='answer') ? true : false }
                                                        onClick={handleShowTab(index, "answer")} 
                                                        startIcon={<QuestionAnswerOutlinedIcon />}>
                                                            Answer
                                                        </Button>
                                                        <Button 
                                                        disabled={ (controlAnswers[index].current_tab_view==="records") ? true : false }
                                                        onClick={handleShowTab(index, "records")} 
                                                        startIcon={<TableRowsRoundedIcon />}>
                                                            Records
                                                        </Button>
                                                        { (typeof answer.chart === "object" && answer.chart.hasOwnProperty("chart_type")) && (
                                                        <Button 
                                                            disabled={ (controlAnswers[index].current_tab_view==='chart') ? true : false }
                                                            onClick={handleShowTab(index, "chart")} 
                                                            startIcon={<InsightsOutlinedIcon />}>
                                                                Chart
                                                        </Button>
                                                        )}                                                        
                                                    </div>
                                                </Fade>
                                            </Grid>
                                            )}

                                            { answer.chart === "loading" && (
                                                <Grid sx={{ display: 'flex', alignItems: 'center' }}>
                                                    <CircularProgress size={16} color="primary" sx={{ p:0, m:0 }} />
                                                    <Typography variant="caption" color="secondaryText" sx={{ pl:2 }} >Generating chart...</Typography>
                                                </Grid>
                                            )}

                                            { answer.chart.hasOwnProperty("rationale") && (
                                                <Typography variant="caption" color="secondaryText" >
                                                    { answer.chart.rationale }
                                                </Typography>
                                            )}

                                        </Grid>
                                    )}

                                </Box>
                            </Box>
                    ) : (
                        <Grid container justifyContent="flex-end">  
                            <Box sx={{ 
                                textAlign: "right", 
                                borderRadius: 4,
                                fontWeight: 500, 
                                pt: 1, pb:1, pl:2, pr: 2, mb: 1, mt: 2, mr:1,
                                boxShadow: 'rgba(0, 0, 0, 0.05) 0px 4px 12px',
                                background: "#B2DFDB"
                                }}>
                                <Typography variant="body1">
                                    { answer.query }
                                </Typography>
                            </Box>
                        </Grid>
                    )}
                    </li>
                ))}

                { loading && (
                <Box sx={{ p:0, pl:1 }}>
                    <Fade timeout={1000} in={loading}>
                    <Stack direction="row" spacing={2} sx={{ display: "flex", alignItems: "center" }}>
                        <CircularProgress size={28} color="primary" sx={{ p:0, m:0 }} />
                        <Box sx={{ 
                            pt:1, pb:1, pl:2, pr: 2, m:0, borderRadius: 4, display: "flex",
                            boxShadow: 'rgba(0, 0, 0, 0.05) 0px 4px 12px',
                            background: "#B2DFDB"
                            }}
                        >
                            <Typography variant="body1">Answering your question...</Typography>
                        </Box>
                    </Stack>
                    </Fade>
                </Box>
                )}
                
                {/* this is the last item that scrolls into view when the effect is run */}
                <li ref={scrollRef} />
            </ul>
            ) : (
            <Box textAlign={"center"} sx={{ pl: 1, pt: 1, pr: 1, pb: 6, height: height, display: "flex", alignItems: "flex-end" }}>
                <div style={{ width: "100%" }}>
                    <img src="/images/Arch_Amazon-Bedrock_64.png" alt="Agents for Amazon Bedrock" />
                    <Typography  variant="h5" sx={{ pb: 1, fontWeight: 500 }}>Agents for Amazon Bedrock</Typography>
                    <Typography sx={{  pb: 4, fontWeight: 400 }}>Enable generative AI applications to execute multi step business tasks using natural language.</Typography>
                    <Typography color="primary" sx={{ fontSize: "1.1rem", pb: 1, fontWeight: 500 }}>{WELCOME_MESSAGE}</Typography>
                </div>
            </Box>
            )}
        </Box>

        <Paper
            component="form"
            sx={(theme) => ({
                zIndex: 0,
                p: 1, mb: 2, display: 'flex', alignItems: 'center', 
                boxShadow: 'rgba(17, 17, 26, 0.05) 0px 4px 16px, rgba(17, 17, 26, 0.05) 0px 8px 24px, rgba(17, 17, 26, 0.05) 0px 16px 56px',
                border: 1,
                borderColor: 'divider',
                borderRadius: 6
            })}
            >
            <Box sx={{ pt:1 }}>
                <img src="/images/AWS_logo_RGB.png" alt="Amazon Web Services" height={20} />
            </Box>
            <InputBase
                required
                id="query"
                name="query"
                placeholder="Type your question..."
                fullWidth
                multiline
                onChange={handleQuery}
                onKeyDown={handleKeyPress}
                value={query}
                variant="outlined"
                inputProps={{ maxLength: MAX_LENGTH_INPUT_SEARCH }}
                sx={{ pl: 1, pr:2 }}
            />
            <Divider sx={{ height: 32 }} orientation="vertical" />
            <IconButton color="primary" sx={{ p: 1 }} aria-label="directions" disabled={!enabled} onClick={handleClick}>
                <SendIcon />
            </IconButton>
        </Paper>

        { selectedAB>0 && (
            <AnswerDetailsDialog open={openAnswerDetails} handleClose={handleCloseAnswerDetails} answer={answers[selectedAB]} question={answers[selectedAB-1].query} runningTraces={answers[selectedB].runningTraces} />
        )}

    </Box>
    );
};

export default Chat;