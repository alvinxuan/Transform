import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import app


BPEL_NAMESPACE = "http://schemas.xmlsoap.org/ws/2003/03/business-process/"

BPMN_XML = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL">
  <process id="Process_1">
    <startEvent id="StartEvent_1" />
    <task id="Task_1" name="Work" />
    <endEvent id="EndEvent_1" name="Done" />
    <sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="Task_1" />
    <sequenceFlow id="Flow_2" sourceRef="Task_1" targetRef="EndEvent_1" />
  </process>
</definitions>
"""


class TransformNamespaceTests(unittest.TestCase):
    def test_generated_bpel_uses_a_bound_bpel_namespace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.bpmn"
            output_path = Path(temp_dir) / "output.xml"
            input_path.write_text(BPMN_XML, encoding="utf-8")

            app.transform(str(input_path), str(output_path))

            try:
                root = ET.parse(output_path).getroot()
            except ET.ParseError as exc:
                self.fail(f"generated BPEL must be namespace-valid XML: {exc}")

            self.assertEqual(root.tag, f"{{{BPEL_NAMESPACE}}}process")
            self.assertIsNotNone(root.find(f"{{{BPEL_NAMESPACE}}}sequence"))


class SequenceBuilderTests(unittest.TestCase):
    @staticmethod
    def make_state(states, state_id, state_type, name=None):
        state = app.State(state_id, name or state_id, state_type)
        states[state_id] = state
        return state

    @staticmethod
    def connect(source, target, event):
        source.add_transition(app.Transition(event, target))

    @staticmethod
    def activity_names(sequence):
        activity_tags = {
            "compensate",
            "empty",
            "exit",
            "invoke",
            "receive",
            "scope",
            "throw",
            "wait",
        }
        return [
            element.get("name")
            for element in sequence.iter()
            if element.tag.rsplit("}", 1)[-1].rsplit(":", 1)[-1] in activity_tags
        ]

    def test_shared_task_after_branches_is_emitted_once(self):
        states = {}
        split = self.make_state(states, "split", "exclusiveGateway", "Split")
        left = self.make_state(states, "left", "Task", "Left")
        right = self.make_state(states, "right", "Task", "Right")
        shared = self.make_state(states, "shared", "Task", "Shared")
        end = self.make_state(states, "end", "endEvent", "End")
        self.connect(split, left, "flow_1")
        self.connect(split, right, "flow_2")
        self.connect(left, shared, "flow_3")
        self.connect(right, shared, "flow_4")
        self.connect(shared, end, "flow_5")

        sequence, _ = app.build_sequence(states, split)

        self.assertEqual(
            self.activity_names(sequence),
            ["Left", "Right", "Shared", "End"],
        )

    def test_outer_merge_survives_a_nested_branch_that_can_terminate(self):
        states = {}
        split = self.make_state(states, "split", "parellelGateway", "Split")
        left = self.make_state(states, "left", "Task", "Left")
        right = self.make_state(states, "right", "Task", "Right")
        decision = self.make_state(
            states, "decision", "exclusiveGateway", "Decision"
        )
        merge = self.make_state(states, "merge", "parellelGateway", "Merge")
        after = self.make_state(states, "after", "Task", "After")
        end = self.make_state(states, "end", "endEvent", "End")
        error = self.make_state(states, "error", "errorEndEvent", "Error")
        self.connect(split, left, "flow_1")
        self.connect(split, right, "flow_2")
        self.connect(left, merge, "flow_3")
        self.connect(right, decision, "flow_4")
        self.connect(decision, merge, "flow_5")
        self.connect(decision, error, "flow_6")
        self.connect(merge, after, "flow_7")
        self.connect(after, end, "flow_8")

        sequence, _ = app.build_sequence(states, split)

        self.assertEqual(
            self.activity_names(sequence),
            ["Left", "Right", "Error", "After", "End"],
        )

    def test_outer_merge_rejects_a_nested_branch_that_ends_normally(self):
        states = {}
        split = self.make_state(states, "split", "parellelGateway", "Split")
        left = self.make_state(states, "left", "Task", "Left")
        right = self.make_state(states, "right", "Task", "Right")
        decision = self.make_state(
            states, "decision", "exclusiveGateway", "Decision"
        )
        merge = self.make_state(states, "merge", "parellelGateway", "Merge")
        after = self.make_state(states, "after", "Task", "After")
        end = self.make_state(states, "end", "endEvent", "End")
        early_end = self.make_state(
            states, "early_end", "endEvent", "EarlyEnd"
        )
        self.connect(split, left, "flow_1")
        self.connect(split, right, "flow_2")
        self.connect(left, merge, "flow_3")
        self.connect(right, decision, "flow_4")
        self.connect(decision, merge, "flow_5")
        self.connect(decision, early_end, "flow_6")
        self.connect(merge, after, "flow_7")
        self.connect(after, end, "flow_8")

        with self.assertRaisesRegex(ValueError, "(?i)unsupported"):
            app.build_sequence(states, split)

    def test_partial_merge_is_rejected_instead_of_duplicating_work(self):
        states = {}
        split = self.make_state(states, "split", "parellelGateway", "Split")
        left = self.make_state(states, "left", "Task", "Left")
        right = self.make_state(states, "right", "Task", "Right")
        solo = self.make_state(states, "solo", "Task", "Solo")
        shared = self.make_state(states, "shared", "Task", "Shared")
        shared_end = self.make_state(
            states, "shared_end", "endEvent", "SharedEnd"
        )
        solo_end = self.make_state(states, "solo_end", "endEvent", "SoloEnd")
        self.connect(split, left, "flow_1")
        self.connect(split, right, "flow_2")
        self.connect(split, solo, "flow_3")
        self.connect(left, shared, "flow_4")
        self.connect(right, shared, "flow_5")
        self.connect(shared, shared_end, "flow_6")
        self.connect(solo, solo_end, "flow_7")

        with self.assertRaisesRegex(ValueError, "partial merge"):
            app.build_sequence(states, split)

    def test_partial_merge_before_a_global_merge_is_rejected(self):
        states = {}
        split = self.make_state(states, "split", "parellelGateway", "Split")
        left = self.make_state(states, "left", "Task", "Left")
        shared = self.make_state(states, "shared", "Task", "Shared")
        merge = self.make_state(states, "merge", "parellelGateway", "Merge")
        end = self.make_state(states, "end", "endEvent", "End")
        self.connect(split, left, "flow_1")
        self.connect(split, shared, "flow_2")
        self.connect(split, merge, "flow_3")
        self.connect(left, shared, "flow_4")
        self.connect(shared, merge, "flow_5")
        self.connect(merge, end, "flow_6")

        with self.assertRaisesRegex(ValueError, "partial merge"):
            app.build_sequence(states, split)

    def test_shared_node_with_a_bypass_path_is_rejected(self):
        states = {}
        outer = self.make_state(states, "outer", "parellelGateway", "Outer")
        nested = self.make_state(states, "nested", "exclusiveGateway", "Nested")
        shared = self.make_state(states, "shared", "Task", "Shared")
        merge = self.make_state(states, "merge", "parellelGateway", "Merge")
        end = self.make_state(states, "end", "endEvent", "End")
        self.connect(outer, nested, "flow_1")
        self.connect(outer, shared, "flow_2")
        self.connect(nested, shared, "flow_3")
        self.connect(nested, merge, "flow_4")
        self.connect(shared, merge, "flow_5")
        self.connect(merge, end, "flow_6")

        with self.assertRaisesRegex(ValueError, "partial merge"):
            app.build_sequence(states, outer)

    def test_one_output_gateway_is_a_pass_through(self):
        states = {}
        gateway = self.make_state(states, "gateway", "exclusiveGateway", "Gateway")
        after = self.make_state(states, "after", "Task", "After")
        end = self.make_state(states, "end", "endEvent", "End")
        self.connect(gateway, after, "flow_1")
        self.connect(after, end, "flow_2")

        try:
            sequence, _ = app.build_sequence(states, gateway)
        except Exception as exc:
            self.fail(f"a one-output gateway must not fail: {exc}")

        self.assertEqual(self.activity_names(sequence), ["After", "End"])

    def test_completed_build_does_not_affect_the_next_build(self):
        first_states = {}
        split = self.make_state(first_states, "split", "exclusiveGateway", "Split")
        left = self.make_state(first_states, "left", "Task", "Left")
        right = self.make_state(first_states, "right", "Task", "Right")
        left_end = self.make_state(first_states, "left_end", "endEvent", "LeftEnd")
        right_end = self.make_state(first_states, "right_end", "endEvent", "RightEnd")
        self.connect(split, left, "flow_1")
        self.connect(split, right, "flow_2")
        self.connect(left, left_end, "flow_3")
        self.connect(right, right_end, "flow_4")
        app.build_sequence(first_states, split)

        second_states = {}
        gateway = self.make_state(second_states, "gateway", "exclusiveGateway", "Gateway")
        after = self.make_state(second_states, "after", "Task", "After")
        end = self.make_state(second_states, "end", "endEvent", "End")
        self.connect(gateway, after, "flow_1")
        self.connect(after, end, "flow_2")

        sequence, _ = app.build_sequence(second_states, gateway)

        self.assertEqual(self.activity_names(sequence), ["After", "End"])

    def test_build_does_not_mutate_end_event_type(self):
        states = {}
        task = self.make_state(states, "task", "Task", "Task")
        end = self.make_state(states, "end", "endEvent", "End")
        self.connect(task, end, "flow_1")

        app.build_sequence(states, task)

        self.assertEqual(end.type, "endEvent")

    def test_unnamed_end_event_uses_its_id_as_a_stable_name(self):
        states = {}
        task = self.make_state(states, "task", "Task", "Task")
        end = app.State("end", None, "endEvent")
        states[end.id] = end
        self.connect(task, end, "flow_1")

        sequence, _ = app.build_sequence(states, task)

        try:
            ET.tostring(sequence, encoding="unicode")
        except TypeError as exc:
            self.fail(f"an unnamed event must still serialize: {exc}")
        self.assertEqual(self.activity_names(sequence), ["Task", "end"])

    def test_cycle_reports_a_clear_error(self):
        states = {}
        split = self.make_state(states, "split", "exclusiveGateway", "Split")
        loop = self.make_state(states, "loop", "Task", "Loop")
        end = self.make_state(states, "end", "endEvent", "End")
        self.connect(split, loop, "flow_1")
        self.connect(split, end, "flow_2")
        self.connect(loop, split, "flow_3")

        try:
            app.build_sequence(states, split)
        except ValueError as exc:
            self.assertIn("cycle", str(exc).lower())
        except Exception as exc:
            self.fail(f"expected a clear cycle error, got {type(exc).__name__}: {exc}")
        else:
            self.fail("expected a cycle error")

    def test_long_cycle_reports_a_clear_error_without_recursion_overflow(self):
        states = {}
        nodes = [
            self.make_state(states, f"node_{index}", "Task")
            for index in range(1100)
        ]
        for index in range(len(nodes) - 1):
            self.connect(nodes[index], nodes[index + 1], f"flow_{index}")
        self.connect(nodes[-1], nodes[0], "flow_back")

        try:
            app.build_sequence(states, nodes[0])
        except ValueError as exc:
            self.assertIn("cycle", str(exc).lower())
        except Exception as exc:
            self.fail(f"expected ValueError, got {type(exc).__name__}: {exc}")
        else:
            self.fail("expected a cycle error")

    def test_long_acyclic_sequence_does_not_overflow_recursion(self):
        states = {}
        nodes = [
            self.make_state(states, f"node_{index}", "Task")
            for index in range(1100)
        ]
        for index in range(len(nodes) - 1):
            self.connect(nodes[index], nodes[index + 1], f"flow_{index}")

        try:
            sequence, _ = app.build_sequence(states, nodes[0])
        except Exception as exc:
            self.fail(f"a long acyclic sequence must build: {type(exc).__name__}: {exc}")

        names = self.activity_names(sequence)
        self.assertEqual(len(names), 1100)
        self.assertEqual(names[0], "node_0")
        self.assertEqual(names[-1], "node_1099")

    def test_excessive_branch_nesting_reports_a_clear_error(self):
        states = {}
        inner_start = self.make_state(states, "leaf", "Task", "Leaf")
        inner_tail = inner_start

        for index in reversed(range(400)):
            split = self.make_state(
                states,
                f"split_{index}",
                "exclusiveGateway",
            )
            side = self.make_state(states, f"side_{index}", "Task")
            merge = self.make_state(
                states,
                f"merge_{index}",
                "exclusiveGateway",
            )
            self.connect(split, inner_start, f"inner_{index}")
            self.connect(split, side, f"side_{index}")
            self.connect(inner_tail, merge, f"inner_merge_{index}")
            self.connect(side, merge, f"side_merge_{index}")
            inner_start = split
            inner_tail = merge

        end = self.make_state(states, "end", "endEvent", "End")
        self.connect(inner_tail, end, "final")

        try:
            app.build_sequence(states, inner_start)
        except ValueError as exc:
            self.assertIn("nesting", str(exc).lower())
        except Exception as exc:
            self.fail(f"expected ValueError, got {type(exc).__name__}: {exc}")
        else:
            self.fail("expected a branch nesting error")

    def test_branch_nesting_budget_is_preserved_inside_a_subprocess(self):
        states = {}

        def nest_branches(prefix, levels, inner_start):
            inner_tail = inner_start
            for index in reversed(range(levels)):
                split = self.make_state(
                    states,
                    f"{prefix}_split_{index}",
                    "exclusiveGateway",
                )
                side = self.make_state(
                    states,
                    f"{prefix}_side_{index}",
                    "Task",
                )
                merge = self.make_state(
                    states,
                    f"{prefix}_merge_{index}",
                    "exclusiveGateway",
                )
                self.connect(split, inner_start, f"{prefix}_inner_{index}")
                self.connect(split, side, f"{prefix}_side_{index}")
                self.connect(
                    inner_tail,
                    merge,
                    f"{prefix}_inner_merge_{index}",
                )
                self.connect(side, merge, f"{prefix}_side_merge_{index}")
                inner_start = split
                inner_tail = merge
            return inner_start, inner_tail

        subprocess_leaf = self.make_state(states, "sub_leaf", "Task", "SubLeaf")
        subprocess_start, subprocess_tail = nest_branches(
            "sub",
            180,
            subprocess_leaf,
        )
        subprocess_end = self.make_state(
            states,
            "sub_end",
            "endEvent",
            "SubEnd",
        )
        self.connect(subprocess_tail, subprocess_end, "sub_final")

        subprocess = self.make_state(
            states,
            "subprocess",
            "subProcessTask",
            "Subprocess",
        )
        subprocess.subprocess = subprocess_start.id
        outer_start, outer_tail = nest_branches("outer", 180, subprocess)
        end = self.make_state(states, "end", "endEvent", "End")
        self.connect(outer_tail, end, "outer_final")

        try:
            app.build_sequence(states, outer_start)
        except ValueError as exc:
            self.assertIn("nesting", str(exc).lower())
        except Exception as exc:
            self.fail(f"expected ValueError, got {type(exc).__name__}: {exc}")
        else:
            self.fail("expected a nesting error")


if __name__ == "__main__":
    unittest.main()
