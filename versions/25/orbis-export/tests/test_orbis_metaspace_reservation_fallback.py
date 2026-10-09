#!/usr/bin/env python3
"""Ensure failed unconstrained Orbis reservations retry through aligned reserve."""

from pathlib import Path

source = (Path(__file__).resolve().parents[2] /
          "src/hotspot/share/memory/memoryReserver.cpp").read_text()
start = source.index("static char* reserve_memory_inner(char* requested_address")
end = source.index("ReservedSpace MemoryReserver::reserve_memory(", start)
body = source[start:end]

assert "#ifdef ORBIS" in body
assert "if (base == nullptr)" in body
assert "return os::reserve_memory_aligned(size, alignment, mem_tag, exec);" in body
assert body.index("if (base == nullptr)") < body.index(
    "return os::reserve_memory_aligned(size, alignment, mem_tag, exec);")

node_source = (Path(__file__).resolve().parents[2] /
               "src/hotspot/share/memory/metaspace/virtualSpaceNode.cpp").read_text()
node_start = node_source.index(
    "VirtualSpaceNode* VirtualSpaceNode::create_node(size_t word_size")
node_end = node_source.index("// Create a node over an existing space", node_start)
node_body = node_source[node_start:node_end]
assert "#ifdef ORBIS" in node_body
assert "reservation_word_size > chunklevel::MAX_CHUNK_WORD_SIZE" in node_body
assert "reservation_word_size / 2" in node_body
assert "rs = MemoryReserver::reserve(" in node_body

print("Orbis metaspace reservation fallback contract passed")
