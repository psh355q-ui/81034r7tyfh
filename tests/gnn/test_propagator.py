
import unittest
import networkx as nx
from backend.gnn.propagator import GraphPropagator

class TestGraphPropagator(unittest.TestCase):
    def setUp(self):
        # Create a simple graph
        # A --(1.0)--> B --(1.0)--> C
        # D (isolated)
        edges = [("A", "B", 1.0), ("B", "C", 1.0)]
        self.propagator = GraphPropagator(decay_factor=0.5)
        self.propagator.build_graph(edges)

    def test_propagation_1hop(self):
        # Event at A with impact 1.0
        # Expected: B receives 1.0 * decay(0.5) = 0.5
        impacts = self.propagator.propagate(source_node="A", initial_impact=1.0)
        
        self.assertAlmostEqual(impacts["A"], 1.0)
        self.assertAlmostEqual(impacts["B"], 0.5)
        self.assertNotIn("D", impacts) # D is isolated

    def test_propagation_2hop(self):
        # Expected: C receives B(0.5) * decay(0.5) = 0.25
        impacts = self.propagator.propagate(source_node="A", initial_impact=1.0)
        
        self.assertAlmostEqual(impacts["C"], 0.25)

    def test_max_hops_limit(self):
        # Force strict 1-hop limit
        self.propagator.max_hops = 1
        impacts = self.propagator.propagate(source_node="A", initial_impact=1.0)
        
        self.assertIn("B", impacts)
        self.assertNotIn("C", impacts) # C is 2-hop, should be ignored

    def test_multi_source(self):
        # Event at A(1.0) and C(1.0)
        # B is connected to both A and C
        # B from A: 0.5, B from C: 0.5 -> Sum: 1.0
        impacts = self.propagator.propagate_batch({"A": 1.0, "C": 1.0})
        
        self.assertAlmostEqual(impacts["B"], 1.0)

if __name__ == '__main__':
    unittest.main()
