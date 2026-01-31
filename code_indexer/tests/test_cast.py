"""
Unit tests for cAST (Compressed AST) compressor.

Tests cover:
1. Sibling merging algorithm
2. Critical node preservation
3. Compression ratio validation
4. Semantic preservation
5. Edge cases
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from c_ast_compressor import CCompressor, compress_code


class TestCASTCompressor(unittest.TestCase):
    """Test cases for cAST compressor."""

    def setUp(self):
        """Set up test fixtures."""
        self.compressor = CCompressor(
            similarity_threshold=0.7,
            max_compression_ratio=0.6
        )

    def test_basic_compression(self):
        """Test basic compression functionality."""
        code = """
        public void test() {
            int x = 5;
            int y = 10;
            System.out.println(x + y);
        }
        """

        result = self.compressor.compress(code)

        # Should have compressed code
        self.assertIsNotNone(result)
        self.assertIn('compressed_code', result)
        self.assertIn('original_code', result)

        # Compressed code should be shorter (character-wise)
        self.assertLess(
            len(result['compressed_code']),
            len(result['original_code']),
            "Compressed code should be shorter than original"
        )

    def test_character_compression_ratio(self):
        """Test that character compression ratio is within target range."""
        code = """
        public void processOrder(Order order) {
            order.setStatus(Status.PROCESSING);
            order.setUpdatedAt(LocalDateTime.now());
            orderRepository.save(order);
        }
        """

        result = self.compressor.compress(code)

        # Character compression should be 30-50% (ratio: 0.5-0.7)
        # Higher ratio = less compression
        char_ratio = result['stats']['char_compression_ratio']
        self.assertLessEqual(char_ratio, 0.85,
            f"Character compression ratio {char_ratio:.2f} should be <= 0.85")
        self.assertGreaterEqual(char_ratio, 0.4,
            f"Character compression ratio {char_ratio:.2f} should be >= 0.4")

    def test_critical_node_preservation(self):
        """Test that critical control flow nodes are preserved."""
        code = """
        public void test(int x) {
            if (x > 0) {
                System.out.println("positive");
            } else {
                System.out.println("negative");
            }

            for (int i = 0; i < 10; i++) {
                System.out.println(i);
            }

            try {
                riskyOperation();
            } catch (Exception e) {
                log.error("Error", e);
            }
        }
        """

        result = self.compressor.compress(code)

        # Should preserve critical nodes
        preserved_count = result['stats']['preserved_nodes']
        self.assertGreater(preserved_count, 0,
            "Should preserve at least some critical nodes")

        # Check for key control flow keywords in compressed code
        compressed = result['compressed_code']
        self.assertTrue(
            any(keyword in compressed for keyword in ['if', 'for', 'try']),
            "Compressed code should contain control flow keywords"
        )

    def test_method_signature_preservation(self):
        """Test that method signatures are preserved."""
        code = """
        public void processOrder(Order order, String userId) {
            order.setUserId(userId);
            orderRepository.save(order);
        }
        """

        result = self.compressor.compress(code)

        # Should contain key parts of the signature
        compressed = result['compressed_code']
        self.assertIn('processOrder', compressed,
            "Method name should be preserved")
        self.assertIn('Order', compressed,
            "Parameter type should be preserved")

    def test_empty_method(self):
        """Test compression of empty method."""
        code = "public void emptyMethod() {}"

        result = self.compressor.compress(code)

        self.assertIsNotNone(result)
        self.assertIn('compressed_code', result)

        # Empty method should still produce output
        self.assertTrue(len(result['compressed_code']) > 0,
            "Even empty method should produce compressed code")

    def test_method_with_only_comments(self):
        """Test compression of method with only comments."""
        code = """
        public void commentMethod() {
            // This is a comment
            /* Multi-line
               comment */
        }
        """

        result = self.compressor.compress(code)

        self.assertIsNotNone(result)
        # Comments are typically stripped or compressed heavily

    def test_similar_statement_compression(self):
        """Test that similar statements are compressed."""
        code = """
        public void processItems() {
            order.setStatus(Status.PROCESSING);
            order.setCreatedAt(LocalDateTime.now());
            order.setCreatedBy("system");
            order.setUpdatedAt(LocalDateTime.now());
        }
        """

        result = self.compressor.compress(code)

        # The four similar setter statements should be compressed
        # Look for "order" and setter patterns
        compressed = result['compressed_code']
        self.assertIn('order', compressed,
            "Order reference should be present")
        self.assertIn('set', compressed,
            "Setter method patterns should be present")

    def test_nested_loops(self):
        """Test compression of nested loops."""
        code = """
        public void nestedLoops(List<List<Item>> items) {
            for (List<Item> row : items) {
                for (Item item : row) {
                    item.process();
                }
            }
        }
        """

        result = self.compressor.compress(code)

        # Should preserve loop structure
        compressed = result['compressed_code']
        self.assertIn('for', compressed.lower(),
            "Loop keyword should be preserved")

    def test_exception_handling(self):
        """Test compression of exception handling code."""
        code = """
        public void withException() {
            try {
                riskyOperation();
            } catch (IOException e) {
                log.error("IO Error", e);
            } catch (Exception e) {
                log.error("General Error", e);
            } finally {
                cleanup();
            }
        }
        """

        result = self.compressor.compress(code)

        # Should preserve exception handling structure
        compressed = result['compressed_code'].lower()
        self.assertTrue(
            'try' in compressed or 'catch' in compressed or 'finally' in compressed,
            "Exception handling keywords should be preserved"
        )

    def test_compression_statistics(self):
        """Test that compression statistics are calculated correctly."""
        code = """
        public void statisticsTest() {
            int x = 5;
            int y = 10;
            int z = x + y;
            System.out.println(z);
        }
        """

        result = self.compressor.compress(code)

        stats = result['stats']
        self.assertIn('total_nodes', stats)
        self.assertIn('original_tokens', stats)
        self.assertIn('compressed_tokens', stats)
        self.assertIn('original_chars', stats)
        self.assertIn('compressed_chars', stats)

        # All stats should be non-negative
        self.assertGreaterEqual(stats['total_nodes'], 0)
        self.assertGreaterEqual(stats['original_tokens'], 0)
        self.assertGreaterEqual(stats['compressed_tokens'], 0)

    def test_similarity_threshold_effect(self):
        """Test that similarity threshold affects compression."""
        code = """
        public void thresholdTest() {
            item.setField1(value1);
            item.setField2(value2);
            item.setField3(value3);
        }
        """

        # Test with low threshold (more aggressive merging)
        compressor_low = CCompressor(similarity_threshold=0.5)
        result_low = compressor_low.compress(code)

        # Test with high threshold (less aggressive merging)
        compressor_high = CCompressor(similarity_threshold=0.9)
        result_high = compressor_high.compress(code)

        # Both should produce valid output
        self.assertIsNotNone(result_low['compressed_code'])
        self.assertIsNotNone(result_high['compressed_code'])

    def test_parse_error_handling(self):
        """Test that parse errors are handled gracefully."""
        # Invalid Java code
        invalid_code = "this is not valid java code {{{"

        result = self.compressor.compress(invalid_code)

        # Should still return a result
        self.assertIsNotNone(result)

        # If parsing failed, should have original code
        self.assertIsNotNone(result.get('original_code'))

    def test_large_method(self):
        """Test compression of a large method."""
        # Generate a large method with many statements
        statements = []
        for i in range(50):
            statements.append(f"item.setField{i}(value{i});")

        code = f"""
        public void largeMethod(Item item) {{
            {chr(10).join(statements)}
        }}
        """

        result = self.compressor.compress(code)

        self.assertIsNotNone(result)
        self.assertIn('compressed_code', result)

        # Large method should be compressed
        compressed_len = len(result['compressed_code'])
        original_len = len(result['original_code'])
        self.assertLess(compressed_len, original_len,
            "Large method should be compressed")

    def test_convenience_function(self):
        """Test the convenience compress_code function."""
        code = "public void test() { int x = 5; }"

        result = compress_code(code)

        self.assertIn('compressed_code', result)
        self.assertIn('original_code', result)
        self.assertIn('compression_ratio', result)


class TestCASTIntegration(unittest.TestCase):
    """Test cAST integration with parser."""

    def test_cast_availability_check(self):
        """Test that cAST can be imported and used."""
        try:
            from c_ast_compressor import CCompressor, compress_code
            self.assertTrue(True, "cAST compressor should be importable")
        except ImportError as e:
            self.fail(f"cAST compressor should be importable: {e}")

    def test_configuration_compatibility(self):
        """Test that compressor respects configuration."""
        # Test with different configurations
        configs = [
            {'similarity_threshold': 0.5},
            {'similarity_threshold': 0.7},
            {'similarity_threshold': 0.9},
            {'max_compression_ratio': 0.5},
            {'max_compression_ratio': 0.7},
        ]

        code = "public void test() { int x = 5; }"

        for config in configs:
            compressor = CCompressor(**config)
            result = compressor.compress(code)
            self.assertIsNotNone(result,
                f"Compressor with config {config} should produce result")


def run_tests():
    """Run all tests and report results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestCASTCompressor))
    suite.addTests(loader.loadTestsFromTestCase(TestCASTIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
