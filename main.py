import program.factory.factory as factory

    
def play(start_game=True, return_game=False):
    """Convenience function to play a game."""
    game_instance = factory.game_factory(start_game)
    if return_game:
        return game_instance

        
if __name__ == '__main__':
    play()
