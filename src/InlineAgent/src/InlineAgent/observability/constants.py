from enum import Enum


class L2Traces(Enum):
    customOrchestrationTrace = "customOrchestrationTrace"
    failureTrace = "failureTrace"
    guardrailTrace = "guardrailTrace"
    orchestrationTrace = "orchestrationTrace"
    postProcessingTrace = "postProcessingTrace"
    preProcessingTrace = "preProcessingTrace"
    routingClassifierTrace = "routingClassifierTrace"


class L3OrchestrationTraces(Enum):
    invocationInput = "invocationInput"
    modelInvocationInput = "modelInvocationInput"
    modelInvocationOutput = "modelInvocationOutput"
    observation = "observation"
    rationale = "rationale"


class L3RoutingClassifierTraces(Enum):
    invocationInput = "invocationInput"
    modelInvocationInput = "modelInvocationInput"
    modelInvocationOutput = "modelInvocationOutput"
    observation = "observation"


class L4InvocationInputTraces(Enum):
    actionGroupInvocationInput = "actionGroupInvocationInput"
    agentCollaboratorInvocationInput = "agentCollaboratorInvocationInput"
    codeInterpreterInvocationInput = "codeInterpreterInvocationInput"
    knowledgeBaseLookupInput = "knowledgeBaseLookupInput"


class L4ObservationTraces(Enum):
    actionGroupInvocationOutput = "actionGroupInvocationOutput"
    agentCollaboratorInvocationOutput = "agentCollaboratorInvocationOutput"
    codeInterpreterInvocationOutput = "codeInterpreterInvocationOutput"
    finalResponse = "finalResponse"
    knowledgeBaseLookupOutput = "knowledgeBaseLookupOutput"
    repromptResponse = "repromptResponse"
