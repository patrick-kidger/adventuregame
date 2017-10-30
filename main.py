import program.factory.factory as factory

    
def play(start_game=True, return_game=False):
    """Convenience function to play a game."""
    maze_game = factory.maze_game_factory(start_game)
    if return_game:
        return maze_game

        
if __name__ == '__main__':
    play()
