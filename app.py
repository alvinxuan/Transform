import xml.etree.ElementTree as ET
from flask import Flask
from flask import request,jsonify
from flask import send_file, make_response
from flask_cors import CORS
import os
from werkzeug.wrappers import Response
from urllib.parse import quote
app = Flask(__name__)
CORS(app, resources=r'/*')

class State:
    def __init__(self, id, name, type, subprocess="null"):
        self.id = id
        self.name = name or id
        self.type = type
        self.route = 0
        self.device = ""
        self.condition = ""
        self.serviceName = ""
        self.url = ""
        self.method = ""
        self.params = ""
        self.function = ""
        self.protocol = ""
        self.transitions = []
        self.subprocess = subprocess

    def add_transition(self, transition):
        self.transitions.append(transition)

    def __repr__(self):
        return f"State({self.name})"

class Transition:
    def __init__(self, event, next_state):
        self.event = event
        self.next_state = next_state
        self.condition = ""

    def __repr__(self):
        return f"Transition({self.event} -> {self.next_state.name})"

class StateMachine:
    def __init__(self, initial_state):
        self.current_state = initial_state

    def handle_event(self, event):
        for transition in self.current_state.transitions:
            if transition.event == event:
                self.current_state = transition.next_state
                print(f"Transition to {self.current_state.name}")
                return
        print(f"No valid transition for event: {event}")

def create_activity(state):
    """将自动机的状态映射为BPEL的活动"""
    if state.type == "userTask":
        return ET.Element("bpel:invoke", {"name": state.name, "device": state.device, "serviceName": state.serviceName,
                                          "url": state.url, "method": state.method, "params": state.params,
                                          "function": state.function, "protocol": state.protocol})
    elif state.type == "serviceTask":
        return ET.Element("bpel:invoke", {"name": state.name, "serviceName": state.serviceName, "url": state.url,
                                          "method": state.method, "params": state.params, "function": state.function,
                                          "protocol": state.protocol, "partnerLink": state.partnerLink,
                                          "operation": state.operation, "variable": state.variable,
                                          "createInstance": state.createInstance, "portType": state.portType,
                                          "inputVariable": state.inputVariable, "outputVariable": state.outputVariable})
    elif state.type == "businessRuleTask":
        return ET.Element("bpel:invoke", {"name": state.name, "serviceName": state.serviceName, "url": state.url,
                                          "method": state.method, "params": state.params, "function": state.function,
                                          "protocol": state.protocol})
    elif state.type == "scriptTask":
        return ET.Element("bpel:invoke", {"name": state.name, "serviceName": state.serviceName, "url": state.url,
                                          "method": state.method, "params": state.params, "function": state.function,
                                          "protocol": state.protocol})
    elif state.type == "sendTask":
        return ET.Element("bpel:invoke", {"name": state.name, "serviceName": state.serviceName, "url": state.url,
                                          "method": state.method, "params": state.params, "function": state.function,
                                          "protocol": state.protocol, "partnerLink": state.partnerLink,
                                          "operation": state.operation, "variable": state.variable,
                                          "createInstance": state.createInstance, "portType": state.portType,
                                          "inputVariable": state.inputVariable, "outputVariable": state.outputVariable})
    elif state.type == "receiveTask":
        return ET.Element("bpel:receive", {"name": state.name, "serviceName": state.serviceName, "url": state.url,
                                           "method": state.method, "params": state.params, "function": state.function,
                                           "protocol": state.protocol, "partnerLink": state.partnerLink,
                                           "operation": state.operation, "variable": state.variable,
                                           "createInstance": state.createInstance, "portType": state.portType,
                                           "inputVariable": state.inputVariable,
                                           "outputVariable": state.outputVariable})
    elif state.type == "manualTask":
        return ET.Element("bpel:invoke", {"name": state.name, "serviceName": state.serviceName, "url": state.url,
                                          "method": state.method, "params": state.params, "function": state.function,
                                          "protocol": state.protocol})
    elif state.type == "Task":
        return ET.Element("bpel:invoke", {"name": state.name, "serviceName": state.serviceName, "url": state.url,
                                          "method": state.method, "params": state.params, "function": state.function,
                                          "protocol": state.protocol})
    elif state.type == "callActivityTask":
        return ET.Element("bpel:scope", {"name": state.name, "serviceName": state.serviceName, "url": state.url,
                                         "method": state.method, "params": state.params, "function": state.function,
                                         "protocol": state.protocol})
    elif state.type == "subProcessTask":
        return ET.Element("bpel:scope", {"name": state.name, "serviceName": state.serviceName, "url": state.url,
                                         "method": state.method, "params": state.params, "function": state.function,
                                         "protocol": state.protocol})
    elif state.type == "messageStartEvent":
        return ET.Element("bpel:receive", {"name": state.name})
    elif state.type == "messageIntermediateThrowEvent":
        return ET.Element("bpel:receive", {"name": state.name})
    elif state.type == "messageIntermediateCatchEvent":
        return ET.Element("bpel:receive", {"name": state.name})
    elif state.type == "timerIntermediateCatchEvent":
        return ET.Element("bpel:wait", {"name": state.name})
    elif state.type == "compensationIntermediateThrowEvent":
        return ET.Element("bpel:compensate", {"name": state.name})
    elif state.type == "compensationIntermediateCatchEvent":
        return ET.Element("bpel:compensate", {"name": state.name})
    elif state.type == "messageBoundaryEvent":
        return ET.Element("bpel:onEvent", {"name": state.name})
    elif state.type == "timerBoundaryEvent":
        return ET.Element("bpel:onAlarm", {"name": state.name})
    elif state.type == "errorBoundaryEvent":
        return ET.Element("bpel:catch", {"name": state.name})
    elif state.type == "compensationBoundaryEvent":
        return ET.Element("bpel:compensationHandler", {"name": state.name})
    elif state.type == "messageEndEvent":
        return ET.Element("bpel:invoke", {"name": state.name})
    elif state.type == "errorEndEvent":
        return ET.Element("bpel:throw", {"name": state.name})
    elif state.type == "compensationEndEvent":
        return ET.Element("bpel:compensate", {"name": state.name})
    elif state.type == "terminateEndEvent":
        return ET.Element("bpel:exit", {"name": state.name})
    elif state.type == "endEvent":
        return ET.Element("bpel:empty", {"name": state.name})
    return None


class SequenceBuilder:
    """Build structured BPEL sequences from one BPMN state graph."""

    _ABORTING_END_TYPES = {"errorEndEvent", "terminateEndEvent"}
    _MAX_STRUCTURE_NESTING = 200

    def __init__(self, states):
        self.states = states
        self._incoming_counts = self._index_incoming_transitions()

    def build(self, start_state):
        self._validate_acyclic(start_state)
        return self._build_segment(
            start_state,
            stop_state=None,
            active_path=set(),
            nesting_depth=0,
        )

    def _index_incoming_transitions(self):
        state_ids = set(self.states)
        incoming_counts = {state_id: 0 for state_id in state_ids}

        for state_id, state in self.states.items():
            for transition in state.transitions:
                target_id = transition.next_state.id
                if target_id not in state_ids:
                    raise ValueError(
                        f"Transition from {state_id} targets unknown state {target_id}"
                    )
                incoming_counts[target_id] += 1

        return incoming_counts

    def _validate_acyclic(self, start_state):
        visiting = set()
        visited = set()
        pending = [(start_state, False)]

        while pending:
            state, exiting = pending.pop()
            if exiting:
                visiting.remove(state.id)
                visited.add(state.id)
                continue
            if state.id in visited:
                continue
            if state.id in visiting:
                raise ValueError(f"BPMN cycle detected at state {state.id}")

            visiting.add(state.id)
            pending.append((state, True))
            for transition in reversed(state.transitions):
                next_state = transition.next_state
                if next_state.id in visiting:
                    raise ValueError(
                        f"BPMN cycle detected at state {next_state.id}"
                    )
                if next_state.id not in visited:
                    pending.append((next_state, False))

    def _find_merge_state(self, split_state):
        distance_maps = [
            self._reachable_distances(transition.next_state)
            for transition in split_state.transitions
        ]
        reachable_from_every_branch = set(distance_maps[0])
        for distances in distance_maps[1:]:
            reachable_from_every_branch.intersection_update(distances)
        reachable_from_every_branch.discard(split_state.id)
        ordered_candidates = sorted(
            reachable_from_every_branch,
            key=lambda state_id: (
                max(distances[state_id] for distances in distance_maps),
                sum(distances[state_id] for distances in distance_maps),
                state_id,
            ),
        )
        for merge_id in ordered_candidates:
            merge_state = self.states[merge_id]
            if all(
                self._all_paths_reach_or_abort(
                    transition.next_state,
                    merge_state,
                )
                for transition in split_state.transitions
            ):
                branch_reachable_sets = [
                    self._reachable_before(
                        transition.next_state,
                        merge_state,
                    )
                    for transition in split_state.transitions
                ]
                self._raise_for_partial_merge(
                    split_state,
                    branch_reachable_sets,
                )
                return merge_state

        if ordered_candidates:
            raise ValueError(
                f"Unsupported branch at state {split_state.id}: "
                "a path ends normally before the merge"
            )

        self._raise_for_partial_merge(
            split_state,
            [set(distances) for distances in distance_maps],
        )

        return None

    def _raise_for_partial_merge(self, split_state, branch_reachable_sets):
        reach_counts = {}
        for reachable in branch_reachable_sets:
            for state_id in reachable:
                reach_counts[state_id] = reach_counts.get(state_id, 0) + 1

        partial_merges = sorted(
            state_id
            for state_id, count in reach_counts.items()
            if count > 1 and self._incoming_counts[state_id] > 1
        )
        if partial_merges:
            raise ValueError(
                f"Unsupported partial merge at state {partial_merges[0]} "
                f"after split {split_state.id}"
            )

    def _all_paths_reach_or_abort(self, start_state, merge_state):
        visited = set()
        pending = [start_state]

        while pending:
            state = pending.pop()
            if state.id == merge_state.id or state.id in visited:
                continue
            visited.add(state.id)

            if not state.transitions:
                if state.type not in self._ABORTING_END_TYPES:
                    return False
                continue
            pending.extend(
                transition.next_state for transition in state.transitions
            )

        return True

    @staticmethod
    def _reachable_distances(start_state):
        distances = {start_state.id: 0}
        pending = [start_state]
        for state in pending:
            for transition in state.transitions:
                next_state = transition.next_state
                if next_state.id not in distances:
                    distances[next_state.id] = distances[state.id] + 1
                    pending.append(next_state)
        return distances

    @staticmethod
    def _reachable_before(start_state, stop_state):
        reachable = set()
        pending = [start_state]

        while pending:
            state = pending.pop()
            if state.id == stop_state.id or state.id in reachable:
                continue
            reachable.add(state.id)
            pending.extend(
                transition.next_state for transition in state.transitions
            )

        return reachable

    def _build_segment(
        self,
        start_state,
        stop_state,
        active_path,
        nesting_depth,
    ):
        if nesting_depth > self._MAX_STRUCTURE_NESTING:
            raise ValueError(
                "Unsupported process nesting: "
                f"more than {self._MAX_STRUCTURE_NESTING} levels"
            )

        sequence = ET.Element("bpel:sequence")
        current_state = start_state
        path = set(active_path)

        while current_state is not None:
            if stop_state is not None and current_state.id == stop_state.id:
                return sequence, current_state
            if current_state.id in path:
                raise ValueError(f"BPMN cycle detected at state {current_state.id}")
            path.add(current_state.id)

            activity = create_activity(current_state)
            if current_state.type == "subProcessTask":
                subprocess_start = self.states[current_state.subprocess]
                self._validate_acyclic(subprocess_start)
                subprocess_sequence, _ = self._build_segment(
                    subprocess_start,
                    stop_state=None,
                    active_path=set(),
                    nesting_depth=nesting_depth + 1,
                )
                activity.append(subprocess_sequence)
            if activity is not None:
                sequence.append(activity)

            transitions = current_state.transitions
            if not transitions:
                return sequence, current_state

            if len(transitions) > 1:
                merge_state = self._find_merge_state(current_state)
                branch_stop = merge_state or stop_state
                sequence.append(
                    self._build_branch_block(
                        current_state,
                        branch_stop,
                        path,
                        nesting_depth,
                    )
                )
                if merge_state is None:
                    if stop_state is not None:
                        return sequence, stop_state
                    return sequence, current_state
                current_state = merge_state
                continue

            current_state = transitions[0].next_state

        return sequence, current_state

    def _build_branch_sequence(
        self,
        transition,
        merge_state,
        active_path,
        nesting_depth,
    ):
        branch_sequence, _ = self._build_segment(
            transition.next_state,
            stop_state=merge_state,
            active_path=active_path,
            nesting_depth=nesting_depth + 1,
        )
        return branch_sequence

    def _build_branch_block(
        self,
        split_state,
        merge_state,
        active_path,
        nesting_depth,
    ):
        transitions = split_state.transitions

        if split_state.type == "exclusiveGateway":
            if_block = ET.Element(
                "bpel:if",
                {"name": f"Decision_{split_state.name}_if"},
            )
            condition = ET.SubElement(if_block, "bpel:condition")
            condition.text = transitions[0].condition
            if_block.append(
                self._build_branch_sequence(
                    transitions[0],
                    merge_state,
                    set(active_path),
                    nesting_depth,
                )
            )

            for transition in transitions[1:-1]:
                elseif_block = ET.SubElement(if_block, "bpel:elseif")
                condition = ET.SubElement(elseif_block, "bpel:condition")
                condition.text = transition.condition
                elseif_block.append(
                    self._build_branch_sequence(
                        transition,
                        merge_state,
                        set(active_path),
                        nesting_depth,
                    )
                )

            else_block = ET.SubElement(if_block, "bpel:else")
            else_block.append(
                self._build_branch_sequence(
                    transitions[-1],
                    merge_state,
                    set(active_path),
                    nesting_depth,
                )
            )
            return if_block

        flow_block = ET.Element("bpel:flow", {"name": split_state.name})
        for transition in transitions:
            branch_sequence = self._build_branch_sequence(
                transition,
                merge_state,
                set(active_path),
                nesting_depth,
            )
            if split_state.type == "inclusiveGateway":
                if_block = ET.Element(
                    "bpel:if",
                    {"name": f"Decision_{split_state.name}_if"},
                )
                condition = ET.SubElement(if_block, "bpel:condition")
                condition.text = transition.condition
                if_block.append(branch_sequence)
                flow_block.append(if_block)
            else:
                flow_block.append(branch_sequence)
        return flow_block


def build_sequence(states, start_state):
    """Build a BPEL sequence without sharing traversal state across requests."""
    return SequenceBuilder(states).build(start_state)


def transform(sendfile, savefile):
    # 解析BPMN XML文件
    # tree = ET.parse('flow_jxzpeasc.bpmn')
    tree = ET.parse(sendfile)
    # tree2 = ET.parse(file)
    root = tree.getroot()
    # root2 = tree2.getroot()

    # 获取命名空间前缀
    namespace = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}

    # 查找所有的流程元素
    process = root.find('bpmn:process', namespace)

    # PartLinks = root2.find('bpmn:partnerLinks', namespace)
    # Variables = root2.find('bpmn:variables', namespace)
    # partLinks = PartLinks.findall('bpmn:partnerLink', namespace)
    # variables = Variables.findall('bpmn:variable', namespace)

    Tasks = process.findall('bpmn:task', namespace)
    userTasks = process.findall('bpmn:userTask', namespace)
    serviceTasks = process.findall('bpmn:serviceTask', namespace)
    businessRuleTasks = process.findall('bpmn:businessRuleTask', namespace)
    scriptTasks = process.findall('bpmn:scriptTask', namespace)
    sendTasks = process.findall('bpmn:sendTask', namespace)
    receiveTasks = process.findall('bpmn:receiveTask', namespace)
    manualTasks = process.findall('bpmn:manualTask', namespace)
    callActivities = process.findall('bpmn:callActivity', namespace)
    subProcesses = process.findall('bpmn:subProcess', namespace)

    exclusiveGateways = process.findall('bpmn:exclusiveGateway', namespace)
    inclusiveGateways = process.findall('bpmn:inclusiveGateway', namespace)
    parellelGateways = process.findall('bpmn:parallelGateway', namespace)
    eventBasedGateways = process.findall('bpmn:eventBasedGateway', namespace)
    complexGateways = process.findall('bpmn:complexGateway', namespace)

    startEvents = process.findall('bpmn:startEvent', namespace)
    intermediateThrowEvents = process.findall('bpmn:intermediateThrowEvent', namespace)
    intermediateCatchEvents = process.findall('bpmn:intermediateCatchEvent', namespace)
    boundaryEvents = process.findall('bpmn:boundaryEvent', namespace)
    endEvents = process.findall('bpmn:endEvent', namespace)

    Flows = process.findall('bpmn:sequenceFlow', namespace)

    states = {}

    if subProcesses is not None:
        for subProcess in subProcesses:
            state_id = subProcess.get('id')
            state_name = subProcess.get('name')
            states_type = "subProcessTask"

            subTasks = subProcess.findall('bpmn:task', namespace)
            subuserTasks = subProcess.findall('bpmn:userTask', namespace)
            subserviceTasks = subProcess.findall('bpmn:serviceTask', namespace)
            subbusinessRuleTasks = subProcess.findall('bpmn:businessRuleTask', namespace)
            subscriptTasks = subProcess.findall('bpmn:scriptTask', namespace)
            subsendTasks = subProcess.findall('bpmn:sendTask', namespace)
            subreceiveTasks = subProcess.findall('bpmn:receiveTask', namespace)
            submanualTasks = subProcess.findall('bpmn:manualTask', namespace)
            subcallActivities = subProcess.findall('bpmn:callActivity', namespace)
            subsubProcesses = subProcess.findall('bpmn:subProcess', namespace)

            subexclusiveGateways = subProcess.findall('bpmn:exclusiveGateway', namespace)
            subinclusiveGateways = subProcess.findall('bpmn:inclusiveGateway', namespace)
            subparellelGateways = subProcess.findall('bpmn:parallelGateway', namespace)
            subeventBasedGateways = subProcess.findall('bpmn:eventBasedGateway', namespace)
            subcomplexGateways = subProcess.findall('bpmn:complexGateway', namespace)

            substartEvents = subProcess.findall('bpmn:startEvent', namespace)
            subintermediateThrowEvents = subProcess.findall('bpmn:intermediateThrowEvent', namespace)
            subintermediateCatchEvents = subProcess.findall('bpmn:intermediateCatchEvent', namespace)
            subboundaryEvents = subProcess.findall('bpmn:boundaryEvent', namespace)
            subendEvents = subProcess.findall('bpmn:endEvent', namespace)

            subFlows = subProcess.findall('bpmn:sequenceFlow', namespace)

            Tasks.extend(subTasks)
            userTasks.extend(subuserTasks)
            serviceTasks.extend(subserviceTasks)
            businessRuleTasks.extend(subbusinessRuleTasks)
            scriptTasks.extend(subscriptTasks)
            sendTasks.extend(subsendTasks)
            receiveTasks.extend(subreceiveTasks)
            manualTasks.extend(submanualTasks)
            callActivities.extend(subcallActivities)
            subProcesses.extend(subsubProcesses)

            exclusiveGateways.extend(subexclusiveGateways)
            inclusiveGateways.extend(subinclusiveGateways)
            parellelGateways.extend(subparellelGateways)
            eventBasedGateways.extend(subeventBasedGateways)
            complexGateways.extend(subcomplexGateways)

            # startEvents.extend(substartEvents)
            intermediateThrowEvents.extend(subintermediateThrowEvents)
            intermediateCatchEvents.extend(subintermediateCatchEvents)
            boundaryEvents.extend(subboundaryEvents)
            endEvents.extend(subendEvents)

            Flows.extend(subFlows)

            states[state_id] = State(state_id, state_name, states_type, substartEvents[0].get('id'))

            if subProcess.find('.//flowable:property[@name="device"]',
                               {'flowable': 'http://flowable.org/bpmn'}) != None:
                states[state_id].device = subProcess.find('.//flowable:property[@name="device"]',
                                                          {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
            if subProcess.find('.//flowable:property[@name="serviceName"]',
                               {'flowable': 'http://flowable.org/bpmn'}) != None:
                states[state_id].serviceName = subProcess.find('.//flowable:property[@name="serviceName"]',
                                                               {'flowable': 'http://flowable.org/bpmn'}).attrib.get(
                    'value')
            if subProcess.find('.//flowable:property[@name="url"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
                states[state_id].url = subProcess.find('.//flowable:property[@name="url"]',
                                                       {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
            if subProcess.find('.//flowable:property[@name="method"]',
                               {'flowable': 'http://flowable.org/bpmn'}) != None:
                states[state_id].method = subProcess.find('.//flowable:property[@name="method"]',
                                                          {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
            if subProcess.find('.//flowable:property[@name="params"]',
                               {'flowable': 'http://flowable.org/bpmn'}) != None:
                states[state_id].params = subProcess.find('.//flowable:property[@name="params"]',
                                                          {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
            if subProcess.find('.//flowable:property[@name="function"]',
                               {'flowable': 'http://flowable.org/bpmn'}) != None:
                states[state_id].function = subProcess.find('.//flowable:property[@name="function"]',
                                                            {'flowable': 'http://flowable.org/bpmn'}).attrib.get(
                    'value')
            if subProcess.find('.//flowable:property[@name="protocol"]',
                               {'flowable': 'http://flowable.org/bpmn'}) != None:
                states[state_id].protocol = subProcess.find('.//flowable:property[@name="protocol"]',
                                                            {'flowable': 'http://flowable.org/bpmn'}).attrib.get(
                    'value')

            for startEvent in substartEvents:
                state_id = startEvent.get('id')
                state_name = startEvent.get('name')
                if startEvent.find('bpmn:messageEventDefinition', namespace) != None:
                    states_type = "messageStartEvent"
                elif startEvent.find('bpmn:signalEventDefinition', namespace) != None:
                    states_type = "signalStartEvent"
                elif startEvent.find('bpmn:timerEventDefinition', namespace) != None:
                    states_type = "timerStartEvent"
                elif startEvent.find('bpmn:errorEventDefinition', namespace) != None:
                    states_type = "errorStartEvent"
                elif startEvent.find('bpmn:compensateEventDefinition', namespace) != None:
                    states_type = "compensationStartEvent"
                elif startEvent.find('bpmn:terminateEventDefinition', namespace) != None:
                    states_type = "terminateStartEvent"
                elif startEvent.find('bpmn:escalationEventDefinition', namespace) != None:
                    states_type = "escalationStartEvent"
                elif startEvent.find('bpmn:linkEventDefinition', namespace) != None:
                    states_type = "linkStartEvent"
                else:
                    states_type = "startEvent"
                states[state_id] = State(state_id, state_name, states_type)


    # 创建任务和事件的状态
    for Task in Tasks:
        state_id = Task.get('id')
        state_name = Task.get('name')
        states_type = "Task"
        states[state_id] = State(state_id, state_name, states_type)
        if Task.find('.//flowable:property[@name="device"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].device = Task.find('.//flowable:property[@name="device"]',
                                                {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if Task.find('.//flowable:property[@name="serviceName"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].serviceName = Task.find('.//flowable:property[@name="serviceName"]',
                                                     {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if Task.find('.//flowable:property[@name="url"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].url = Task.find('.//flowable:property[@name="url"]',
                                             {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if Task.find('.//flowable:property[@name="method"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].method = Task.find('.//flowable:property[@name="method"]',
                                                {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if Task.find('.//flowable:property[@name="params"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].params = Task.find('.//flowable:property[@name="params"]',
                                                {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if Task.find('.//flowable:property[@name="function"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].function = Task.find('.//flowable:property[@name="function"]',
                                                  {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if Task.find('.//flowable:property[@name="protocol"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].protocol = Task.find('.//flowable:property[@name="protocol"]',
                                                  {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')

    for userTask in userTasks:
        state_id = userTask.get('id')
        state_name = userTask.get('name')
        states_type = "userTask"
        states[state_id] = State(state_id, state_name, states_type)
        if userTask.find('.//flowable:property[@name="device"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].device = userTask.find('.//flowable:property[@name="device"]',
                                                    {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if userTask.find('.//flowable:property[@name="serviceName"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].serviceName = userTask.find('.//flowable:property[@name="serviceName"]',
                                                         {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if userTask.find('.//flowable:property[@name="url"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].url = userTask.find('.//flowable:property[@name="url"]',
                                                 {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if userTask.find('.//flowable:property[@name="method"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].method = userTask.find('.//flowable:property[@name="method"]',
                                                    {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if userTask.find('.//flowable:property[@name="params"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].params = userTask.find('.//flowable:property[@name="params"]',
                                                    {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if userTask.find('.//flowable:property[@name="function"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].function = userTask.find('.//flowable:property[@name="function"]',
                                                      {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if userTask.find('.//flowable:property[@name="protocol"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].protocol = userTask.find('.//flowable:property[@name="protocol"]',
                                                      {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')

    for serviceTask in serviceTasks:
        state_id = serviceTask.get('id')
        state_name = serviceTask.get('name')
        states_type = "serviceTask"
        states[state_id] = State(state_id, state_name, states_type)
        if serviceTask.find('.//flowable:property[@name="device"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].device = serviceTask.find('.//flowable:property[@name="device"]',
                                                       {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if serviceTask.find('.//flowable:property[@name="serviceName"]',
                            {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].serviceName = serviceTask.find('.//flowable:property[@name="serviceName"]',
                                                            {'flowable': 'http://flowable.org/bpmn'}).attrib.get(
                'value')
        if serviceTask.find('.//flowable:property[@name="url"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].url = serviceTask.find('.//flowable:property[@name="url"]',
                                                    {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if serviceTask.find('.//flowable:property[@name="method"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].method = serviceTask.find('.//flowable:property[@name="method"]',
                                                       {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if serviceTask.find('.//flowable:property[@name="params"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].params = serviceTask.find('.//flowable:property[@name="params"]',
                                                       {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if serviceTask.find('.//flowable:property[@name="function"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].function = serviceTask.find('.//flowable:property[@name="function"]',
                                                         {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if serviceTask.find('.//flowable:property[@name="protocol"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].protocol = serviceTask.find('.//flowable:property[@name="protocol"]',
                                                         {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if serviceTask.find('.//flowable:property[@name="partnerLink"]',
                            {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].partnerLink = serviceTask.find('.//flowable:property[@name="partnerLink"]',
                                                            {'flowable': 'http://flowable.org/bpmn'}).attrib.get(
                'value')
        if serviceTask.find('.//flowable:property[@name="operation"]',
                            {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].operation = serviceTask.find('.//flowable:property[@name="operation"]',
                                                          {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if serviceTask.find('.//flowable:property[@name="portType"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].portType = serviceTask.find('.//flowable:property[@name="portType"]',
                                                         {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if serviceTask.find('.//flowable:property[@name="variable"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].variable = serviceTask.find('.//flowable:property[@name="variable"]',
                                                         {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if serviceTask.find('.//flowable:property[@name="createInstance"]',
                            {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].createInstance = serviceTask.find('.//flowable:property[@name="createInstance"]',
                                                               {'flowable': 'http://flowable.org/bpmn'}).attrib.get(
                'value')
        if serviceTask.find('.//flowable:property[@name="inputVariable"]',
                            {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].inputVariable = serviceTask.find('.//flowable:property[@name="inputVariable"]',
                                                              {'flowable': 'http://flowable.org/bpmn'}).attrib.get(
                'value')
        if serviceTask.find('.//flowable:property[@name="outputVariable"]',
                            {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].outputVariable = serviceTask.find('.//flowable:property[@name="outputVariable"]',
                                                               {'flowable': 'http://flowable.org/bpmn'}).attrib.get(
                'value')

    for businessRuleTask in businessRuleTasks:
        state_id = businessRuleTask.get('id')
        state_name = businessRuleTask.get('name')
        states_type = "businessRuleTask"
        states[state_id] = State(state_id, state_name, states_type)
        if Task.find('.//flowable:property[@name="device"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].device = Task.find('.//flowable:property[@name="device"]',
                                                {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if Task.find('.//flowable:property[@name="serviceName"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].serviceName = Task.find('.//flowable:property[@name="serviceName"]',
                                                     {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if Task.find('.//flowable:property[@name="url"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].url = Task.find('.//flowable:property[@name="url"]',
                                             {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if Task.find('.//flowable:property[@name="method"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].method = Task.find('.//flowable:property[@name="method"]',
                                                {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if Task.find('.//flowable:property[@name="params"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].params = Task.find('.//flowable:property[@name="params"]',
                                                {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if Task.find('.//flowable:property[@name="function"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].function = Task.find('.//flowable:property[@name="function"]',
                                                  {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if Task.find('.//flowable:property[@name="protocol"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].protocol = Task.find('.//flowable:property[@name="protocol"]',
                                                  {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')

    for scriptTask in scriptTasks:
        state_id = scriptTask.get('id')
        state_name = scriptTask.get('name')
        states_type = "scriptTask"
        states[state_id] = State(state_id, state_name, states_type)
        if scriptTask.find('.//flowable:property[@name="device"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].device = scriptTask.find('.//flowable:property[@name="device"]',
                                                      {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if scriptTask.find('.//flowable:property[@name="serviceName"]',
                           {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].serviceName = scriptTask.find('.//flowable:property[@name="serviceName"]',
                                                           {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if scriptTask.find('.//flowable:property[@name="url"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].url = scriptTask.find('.//flowable:property[@name="url"]',
                                                   {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if scriptTask.find('.//flowable:property[@name="method"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].method = scriptTask.find('.//flowable:property[@name="method"]',
                                                      {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if scriptTask.find('.//flowable:property[@name="params"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].params = scriptTask.find('.//flowable:property[@name="params"]',
                                                      {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if scriptTask.find('.//flowable:property[@name="function"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].function = scriptTask.find('.//flowable:property[@name="function"]',
                                                        {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if scriptTask.find('.//flowable:property[@name="protocol"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].protocol = scriptTask.find('.//flowable:property[@name="protocol"]',
                                                        {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')

    for sendTask in sendTasks:
        state_id = sendTask.get('id')
        state_name = sendTask.get('name')
        states_type = "sendTask"
        states[state_id] = State(state_id, state_name, states_type)
        if sendTask.find('.//flowable:property[@name="device"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].device = sendTask.find('.//flowable:property[@name="device"]',
                                                    {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if sendTask.find('.//flowable:property[@name="serviceName"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].serviceName = sendTask.find('.//flowable:property[@name="serviceName"]',
                                                         {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if sendTask.find('.//flowable:property[@name="url"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].url = sendTask.find('.//flowable:property[@name="url"]',
                                                 {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if sendTask.find('.//flowable:property[@name="method"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].method = sendTask.find('.//flowable:property[@name="method"]',
                                                    {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if sendTask.find('.//flowable:property[@name="params"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].params = sendTask.find('.//flowable:property[@name="params"]',
                                                    {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if sendTask.find('.//flowable:property[@name="function"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].function = sendTask.find('.//flowable:property[@name="function"]',
                                                      {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if sendTask.find('.//flowable:property[@name="protocol"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].protocol = sendTask.find('.//flowable:property[@name="protocol"]',
                                                      {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if sendTask.find('.//flowable:property[@name="partnerLink"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].partnerLink = sendTask.find('.//flowable:property[@name="partnerLink"]',
                                                         {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if sendTask.find('.//flowable:property[@name="operation"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].operation = sendTask.find('.//flowable:property[@name="operation"]',
                                                       {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if sendTask.find('.//flowable:property[@name="portType"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].portType = sendTask.find('.//flowable:property[@name="portType"]',
                                                      {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if sendTask.find('.//flowable:property[@name="variable"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].variable = sendTask.find('.//flowable:property[@name="variable"]',
                                                      {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if sendTask.find('.//flowable:property[@name="createInstance"]',
                         {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].createInstance = sendTask.find('.//flowable:property[@name="createInstance"]',
                                                            {'flowable': 'http://flowable.org/bpmn'}).attrib.get(
                'value')
        if sendTask.find('.//flowable:property[@name="inputVariable"]',
                         {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].inputVariable = sendTask.find('.//flowable:property[@name="inputVariable"]',
                                                           {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if sendTask.find('.//flowable:property[@name="outputVariable"]',
                         {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].outputVariable = sendTask.find('.//flowable:property[@name="outputVariable"]',
                                                            {'flowable': 'http://flowable.org/bpmn'}).attrib.get(
                'value')

    for receiveTask in receiveTasks:
        state_id = receiveTask.get('id')
        state_name = receiveTask.get('name')
        states_type = "receiveTask"
        states[state_id] = State(state_id, state_name, states_type)
        if receiveTask.find('.//flowable:property[@name="device"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].device = receiveTask.find('.//flowable:property[@name="device"]',
                                                       {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if receiveTask.find('.//flowable:property[@name="serviceName"]',
                            {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].serviceName = receiveTask.find('.//flowable:property[@name="serviceName"]',
                                                            {'flowable': 'http://flowable.org/bpmn'}).attrib.get(
                'value')
        if receiveTask.find('.//flowable:property[@name="url"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].url = receiveTask.find('.//flowable:property[@name="url"]',
                                                    {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if receiveTask.find('.//flowable:property[@name="method"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].method = receiveTask.find('.//flowable:property[@name="method"]',
                                                       {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if receiveTask.find('.//flowable:property[@name="params"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].params = receiveTask.find('.//flowable:property[@name="params"]',
                                                       {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if receiveTask.find('.//flowable:property[@name="function"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].function = receiveTask.find('.//flowable:property[@name="function"]',
                                                         {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if receiveTask.find('.//flowable:property[@name="protocol"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].protocol = receiveTask.find('.//flowable:property[@name="protocol"]',
                                                         {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if receiveTask.find('.//flowable:property[@name="partnerLink"]',
                            {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].partnerLink = receiveTask.find('.//flowable:property[@name="partnerLink"]',
                                                            {'flowable': 'http://flowable.org/bpmn'}).attrib.get(
                'value')
        if receiveTask.find('.//flowable:property[@name="operation"]',
                            {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].operation = receiveTask.find('.//flowable:property[@name="operation"]',
                                                          {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if receiveTask.find('.//flowable:property[@name="portType"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].portType = receiveTask.find('.//flowable:property[@name="portType"]',
                                                         {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if receiveTask.find('.//flowable:property[@name="variable"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].variable = receiveTask.find('.//flowable:property[@name="variable"]',
                                                         {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if receiveTask.find('.//flowable:property[@name="createInstance"]',
                            {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].createInstance = receiveTask.find('.//flowable:property[@name="createInstance"]',
                                                               {'flowable': 'http://flowable.org/bpmn'}).attrib.get(
                'value')
        if receiveTask.find('.//flowable:property[@name="inputVariable"]',
                            {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].inputVariable = receiveTask.find('.//flowable:property[@name="inputVariable"]',
                                                              {'flowable': 'http://flowable.org/bpmn'}).attrib.get(
                'value')
        if receiveTask.find('.//flowable:property[@name="outputVariable"]',
                            {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].outputVariable = receiveTask.find('.//flowable:property[@name="outputVariable"]',
                                                               {'flowable': 'http://flowable.org/bpmn'}).attrib.get(
                'value')

    for manualTask in manualTasks:
        state_id = manualTask.get('id')
        state_name = manualTask.get('name')
        states_type = "manualTask"
        states[state_id] = State(state_id, state_name, states_type)
        if manualTask.find('.//flowable:property[@name="device"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].device = manualTask.find('.//flowable:property[@name="device"]',
                                                      {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if manualTask.find('.//flowable:property[@name="serviceName"]',
                           {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].serviceName = manualTask.find('.//flowable:property[@name="serviceName"]',
                                                           {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if manualTask.find('.//flowable:property[@name="url"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].url = manualTask.find('.//flowable:property[@name="url"]',
                                                   {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if manualTask.find('.//flowable:property[@name="method"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].method = manualTask.find('.//flowable:property[@name="method"]',
                                                      {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if manualTask.find('.//flowable:property[@name="params"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].params = manualTask.find('.//flowable:property[@name="params"]',
                                                      {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if manualTask.find('.//flowable:property[@name="function"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].function = manualTask.find('.//flowable:property[@name="function"]',
                                                        {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if manualTask.find('.//flowable:property[@name="protocol"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].protocol = manualTask.find('.//flowable:property[@name="protocol"]',
                                                        {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')

    for callActivity in callActivities:
        state_id = callActivity.get('id')
        state_name = callActivity.get('name')
        states_type = "callActivityTask"
        states[state_id] = State(state_id, state_name, states_type)
        if callActivity.find('.//flowable:property[@name="device"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].device = callActivity.find('.//flowable:property[@name="device"]',
                                                        {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if callActivity.find('.//flowable:property[@name="serviceName"]',
                             {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].serviceName = callActivity.find('.//flowable:property[@name="serviceName"]',
                                                             {'flowable': 'http://flowable.org/bpmn'}).attrib.get(
                'value')
        if callActivity.find('.//flowable:property[@name="url"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].url = callActivity.find('.//flowable:property[@name="url"]',
                                                     {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if callActivity.find('.//flowable:property[@name="method"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].method = callActivity.find('.//flowable:property[@name="method"]',
                                                        {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if callActivity.find('.//flowable:property[@name="params"]', {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].params = callActivity.find('.//flowable:property[@name="params"]',
                                                        {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if callActivity.find('.//flowable:property[@name="function"]',
                             {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].function = callActivity.find('.//flowable:property[@name="function"]',
                                                          {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')
        if callActivity.find('.//flowable:property[@name="protocol"]',
                             {'flowable': 'http://flowable.org/bpmn'}) != None:
            states[state_id].protocol = callActivity.find('.//flowable:property[@name="protocol"]',
                                                          {'flowable': 'http://flowable.org/bpmn'}).attrib.get('value')


    for startEvent in startEvents:
        state_id = startEvent.get('id')
        state_name = startEvent.get('name')
        if startEvent.find('bpmn:messageEventDefinition', namespace) != None:
            states_type = "messageStartEvent"
        elif startEvent.find('bpmn:signalEventDefinition', namespace) != None:
            states_type = "signalStartEvent"
        elif startEvent.find('bpmn:timerEventDefinition', namespace) != None:
            states_type = "timerStartEvent"
        elif startEvent.find('bpmn:errorEventDefinition', namespace) != None:
            states_type = "errorStartEvent"
        elif startEvent.find('bpmn:compensateEventDefinition', namespace) != None:
            states_type = "compensationStartEvent"
        elif startEvent.find('bpmn:terminateEventDefinition', namespace) != None:
            states_type = "terminateStartEvent"
        elif startEvent.find('bpmn:escalationEventDefinition', namespace) != None:
            states_type = "escalationStartEvent"
        elif startEvent.find('bpmn:linkEventDefinition', namespace) != None:
            states_type = "linkStartEvent"
        else:
            states_type = "startEvent"
        # print(states_type)
        states[state_id] = State(state_id, state_name, states_type)

    for intermediateThrowEvent in intermediateThrowEvents:
        state_id = intermediateThrowEvent.get('id')
        state_name = intermediateThrowEvent.get('name')
        if intermediateThrowEvent.find('bpmn:messageEventDefinition', namespace) != None:
            states_type = "messageIntermediateThrowEvent"
        elif intermediateThrowEvent.find('bpmn:signalEventDefinition', namespace) != None:
            states_type = "signalIntermediateThrowEvent"
        elif intermediateThrowEvent.find('bpmn:timerEventDefinition', namespace) != None:
            states_type = "timerIntermediateThrowEvent"
        elif intermediateThrowEvent.find('bpmn:errorEventDefinition', namespace) != None:
            states_type = "errorIntermediateThrowEvent"
        elif intermediateThrowEvent.find('bpmn:compensateEventDefinition', namespace) != None:
            states_type = "compensationIntermediateThrowEvent"
        elif intermediateThrowEvent.find('bpmn:terminateEventDefinition', namespace) != None:
            states_type = "terminateIntermediateThrowEvent"
        elif intermediateThrowEvent.find('bpmn:escalationEventDefinition', namespace) != None:
            states_type = "escalationIntermediateThrowEvent"
        elif intermediateThrowEvent.find('bpmn:linkEventDefinition', namespace) != None:
            states_type = "linkIntermediateThrowEvent"
        else:
            states_type = "intermediateThrowEvent"
        # print(states_type)
        states[state_id] = State(state_id, state_name, states_type)

    for intermediateCatchEvent in intermediateCatchEvents:
        state_id = intermediateCatchEvent.get('id')
        state_name = intermediateCatchEvent.get('name')
        if intermediateCatchEvent.find('bpmn:messageEventDefinition', namespace) != None:
            states_type = "messageIntermediateCatchEvent"
        elif intermediateCatchEvent.find('bpmn:signalEventDefinition', namespace) != None:
            states_type = "signalIntermediateCatchEvent"
        elif intermediateCatchEvent.find('bpmn:timerEventDefinition', namespace) != None:
            states_type = "timerIntermediateCatchEvent"
        elif intermediateCatchEvent.find('bpmn:errorEventDefinition', namespace) != None:
            states_type = "errorIntermediateCatchEvent"
        elif intermediateCatchEvent.find('bpmn:compensateEventDefinition', namespace) != None:
            states_type = "compensationIntermediateCatchEvent"
        elif intermediateCatchEvent.find('bpmn:terminateEventDefinition', namespace) != None:
            states_type = "terminateIntermediateCatchEvent"
        elif intermediateCatchEvent.find('bpmn:escalationEventDefinition', namespace) != None:
            states_type = "escalationIntermediateCatchEvent"
        elif intermediateCatchEvent.find('bpmn:linkEventDefinition', namespace) != None:
            states_type = "linkIntermediateCatchEvent"
        else:
            states_type = "intermediateCatchEvent"
        # print(states_type)
        states[state_id] = State(state_id, state_name, states_type)

    for boundaryEvent in boundaryEvents:
        state_id = boundaryEvent.get('id')
        state_name = boundaryEvent.get('name')
        if boundaryEvent.find('bpmn:messageEventDefinition', namespace) != None:
            states_type = "messageBoundaryEvent"
        elif boundaryEvent.find('bpmn:signalEventDefinition', namespace) != None:
            states_type = "signalBoundaryEvent"
        elif boundaryEvent.find('bpmn:timerEventDefinition', namespace) != None:
            states_type = "timerBoundaryEvent"
        elif boundaryEvent.find('bpmn:errorEventDefinition', namespace) != None:
            states_type = "errorBoundaryEvent"
        elif boundaryEvent.find('bpmn:compensateEventDefinition', namespace) != None:
            states_type = "compensationBoundaryEvent"
        elif boundaryEvent.find('bpmn:terminateEventDefinition', namespace) != None:
            states_type = "terminateBoundaryEvent"
        elif boundaryEvent.find('bpmn:escalationEventDefinition', namespace) != None:
            states_type = "escalationBoundaryEvent"
        elif boundaryEvent.find('bpmn:linkEventDefinition', namespace) != None:
            states_type = "linkBoundaryEvent"
        else:
            states_type = "boundaryEvent"
        # print(states_type)
        flow = {
            "id": str(boundaryEvent.get('attachedToRef')) + '_' + str(state_id),
            "sourceRef": boundaryEvent.get('attachedToRef'),
            "targetRef": state_id
        }
        Flows.append(flow)
        states[state_id] = State(state_id, state_name, states_type)

    for endEvent in endEvents:
        state_id = endEvent.get('id')
        state_name = endEvent.get('name')
        if endEvent.find('bpmn:messageEventDefinition', namespace) != None:
            states_type = "messageEndEvent"
        elif endEvent.find('bpmn:signalEventDefinition', namespace) != None:
            states_type = "signalEndEvent"
        elif endEvent.find('bpmn:timerEventDefinition', namespace) != None:
            states_type = "timerEndEvent"
        elif endEvent.find('bpmn:errorEventDefinition', namespace) != None:
            states_type = "errorEndEvent"
        elif endEvent.find('bpmn:compensateEventDefinition', namespace) != None:
            states_type = "compensationEndEvent"
        elif endEvent.find('bpmn:terminateEventDefinition', namespace) != None:
            states_type = "terminateEndEvent"
        elif endEvent.find('bpmn:escalationEventDefinition', namespace) != None:
            states_type = "escalationEndEvent"
        elif endEvent.find('bpmn:linkEventDefinition', namespace) != None:
            states_type = "linkEndEvent"
        else:
            states_type = "endEvent"
        # print(states_type)
        states[state_id] = State(state_id, state_name, states_type)

    for exclusiveGateway in exclusiveGateways:
        state_id = exclusiveGateway.get('id')
        state_name = exclusiveGateway.get('name')
        states_type = "exclusiveGateway"
        states[state_id] = State(state_id, state_name, states_type)
        states[state_id].route = 2

    for inclusiveGateway in inclusiveGateways:
        state_id = inclusiveGateway.get('id')
        state_name = inclusiveGateway.get('name')
        states_type = "inclusiveGateway"
        states[state_id] = State(state_id, state_name, states_type)
        states[state_id].route = 3

    for parellelGateway in parellelGateways:
        state_id = parellelGateway.get('id')
        state_name = parellelGateway.get('name')
        states_type = "parellelGateway"
        states[state_id] = State(state_id, state_name, states_type)
        states[state_id].route = 3

    for eventBasedGateway in eventBasedGateways:
        state_id = eventBasedGateway.get('id')
        state_name = eventBasedGateway.get('name')
        states_type = "eventBasedGateway"
        states[state_id] = State(state_id, state_name, states_type)
        states[state_id].route = 2

    for complexGateway in complexGateways:
        state_id = complexGateway.get('id')
        state_name = complexGateway.get('name')
        states_type = "complexGateway"
        states[state_id] = State(state_id, state_name, states_type)
        states[state_id].route = 2

    # 创建状态转换
    for Flow in Flows:
        source_ref = Flow.get('sourceRef')
        target_ref = Flow.get('targetRef')
        flow_id = Flow.get('id')

        # 在源状态中添加转换
        if source_ref in states and target_ref in states:
            source_state = states[source_ref]
            target_state = states[target_ref]
            transition = Transition(event=flow_id, next_state=target_state)
            if type(Flow) != dict and Flow.find('bpmn:conditionExpression', namespace) != None:
                transition.condition = Flow.find('bpmn:conditionExpression', namespace).text
            source_state.add_transition(transition)

    # 初始化BPEL结构
    bpel_ns = "http://schemas.xmlsoap.org/ws/2003/03/business-process/"
    process = ET.Element("bpel:process", {
        "name": savefile[0:-4],
        "xmlns:bpel": bpel_ns,
        "targetNamespace": "http://example.com/bpel"
    })

    for startEvent in startEvents:
        start = startEvent.get('id')
        break
    # 构建整个BPEL流程
    main_sequence, _ = build_sequence(states, states[start])
    # partlinks = ET.Element("bpel:partnerLinks")
    # for partLink in partLinks:
    #     partLink = ET.SubElement(partlinks, "bpel:partnerLink",
    #                              {"name": partLink.get('name'), "partnerLinkType": partLink.get('partnerLinkType'),
    #                               "myRole": partLink.get('myRole'), "partnerRole": partLink.get('partnerRole')})
    # ariables = ET.Element("bpel:variables")
    # for ariable in variables:
    #     ariable = ET.SubElement(ariables, "bpel:variable",
    #                             {"name": ariable.get('name'), "messageType": ariable.get('messageType')})
    # process.append(partlinks)
    # process.append(ariables)
    process.append(main_sequence)

    # 转化为字符串并保存为XML
    tree = ET.ElementTree(process)
    tree.write(savefile, encoding="utf-8", xml_declaration=True)
    # tree.write("generated_bpel2.xml", encoding="utf-8", xml_declaration=True)

    return tree


@app.route('/bpmn2bpel',methods=['POST'])
def bpmn2bpel():
    try:
        # 获取地址
        bpmn_path = request.json.get('bpmnpath')
        # print(bpmn_path)
        # 判断地址是否为空
        if not bpmn_path:
            return jsonify({"bpelpath": None, "error": "No BPMN file name provided in URL"},400)
        # 生成bpel文件地址
        # file_name_without_ext = os.path.splitext(os.path.basename(bpmn_path))[0]
        file_name_without_ext = bpmn_path[0:-4]
        bpel_path = f"{file_name_without_ext}_bpel.xml"
        # print(bpel_path)
        # 开始转换
        transform(bpmn_path, bpel_path)
        # print(1111111111111)
        # print("bpelpath"+os.path.splitext(os.path.basename(bpel_path))[0] + ".xml")
        return jsonify({"bpelpath": os.path.splitext(os.path.basename(bpel_path))[0] + ".xml"})

    except Exception as e:
        return jsonify({"bpelpath": None, "error": str(e)}, 500)

@app.route('/downloadBpel',methods=['POST'])
def download_xml():
    try:
        bpel_path = "/home/industrial-project/kai/java/transform/"+request.json.get('bpelpath')

        # 读取XML内容
        with open(bpel_path, 'r', encoding='utf-8') as f:
            bpel_content = f.read()

        # 创建响应对象
        response = Response(bpel_content, mimetype='application/octet-stream; charset=utf-8')
        encoded_filename = quote(os.path.basename(bpel_path).encode('utf-8'))
        response.headers['Content-Type'] = 'application/octet-stream; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'
        return response
        # return jsonify({"data": str(bpel_content)})

    except Exception as e:
        return jsonify({"error": str(e)}, 500)


if __name__ == "__main__":
    app.run(host='202.120.119.227', port=64334)
    # transform("多任务组合.bpmn20.xml", "多任务组合.bpmn20_bpel.xml")
    # transform("case5.bpmn", "generated_bpel6.xml")
    # transform("工业流程.bpmn20.xml", "工业流程bpel.xml")
