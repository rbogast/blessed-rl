"""
Prefab manager that coordinates prefab spawning with world generation.
"""

import random
from typing import Set, Dict, Any
from .loader import PrefabLoader
from .spawner import PrefabSpawner


class PrefabManager:
    """Manages prefab spawning timing and coordination with world generation."""
    
    def __init__(self, world, world_generator, message_log=None):
        self.world = world
        self.world_generator = world_generator
        self.message_log = message_log
        
        # Load prefabs
        self.loader = PrefabLoader()
        self.spawner = PrefabSpawner(world, world_generator)
        
        # Track which chunks have been processed for prefabs
        self.processed_chunks: Set[int] = set()
        
        # Master RNG for prefab spawning (separate from world generation)
        self.prefab_rng = random.Random(world_generator.seed + 999999)
    
    def update_for_chunk_generation(self, new_chunk_id: int) -> None:
        """Called when a new chunk is generated. Processes prefabs for the previous chunk."""
        # Process prefabs for the chunk one behind the newly generated chunk
        target_chunk_id = new_chunk_id - 1
        
        if target_chunk_id >= 0 and target_chunk_id not in self.processed_chunks:
            self._process_chunk_prefabs(target_chunk_id)
            self.processed_chunks.add(target_chunk_id)
    
    def _process_chunk_prefabs(self, chunk_id: int) -> None:
        """Process prefab spawning for a specific chunk."""
        if not self.loader.prefabs:
            return  # No prefabs loaded
        
        # Create a deterministic RNG for this chunk
        chunk_rng = random.Random(self.world_generator.seed + chunk_id + 888888)
        
        spawned_count = 0
        
        # Try to spawn each prefab type
        for prefab_id, prefab in self.loader.prefabs.items():
            # Roll for spawn chance
            if chunk_rng.random() < prefab.spawn_chance:
                success = self.spawner.try_spawn_prefab(prefab, chunk_id, chunk_rng)
                if success:
                    spawned_count += 1
        
        if spawned_count > 0 and self.message_log:
            self.message_log.add_info(f"Placed {spawned_count} prefabs in chunk {chunk_id}")
    
    def force_process_chunk(self, chunk_id: int) -> None:
        """Force processing of prefabs for a specific chunk (for testing)."""
        if chunk_id not in self.processed_chunks:
            self._process_chunk_prefabs(chunk_id)
            self.processed_chunks.add(chunk_id)
    
    def get_prefab_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded prefabs."""
        return {
            'loaded_prefabs': len(self.loader.prefabs),
            'prefab_ids': list(self.loader.prefabs.keys()),
            'processed_chunks': len(self.processed_chunks),
            'processed_chunk_ids': sorted(list(self.processed_chunks))
        }
    
    def reload_prefabs(self) -> None:
        """Reload prefab definitions from file."""
        self.loader.reload()
        if self.message_log:
            self.message_log.add_system(f"Reloaded {len(self.loader.prefabs)} prefabs")
    
    def reset(self) -> None:
        """Reset the prefab manager (for game restart)."""
        self.processed_chunks.clear()
        self.prefab_rng = random.Random(self.world_generator.seed + 999999)
