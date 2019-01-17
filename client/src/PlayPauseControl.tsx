import React from "react";
import {
    CurrentPlayerState,
    playerState,
    playlistChanged,
    PlaylistItem,
    playNextTrack,
    playPreviousTrack,
    togglePlayPause
} from "./api";

import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core/styles";
import Button from '@material-ui/core/Button';
import PlayArrow from '@material-ui/icons/PlayArrowRounded';
import Pause from '@material-ui/icons/PauseRounded';
import Previous from '@material-ui/icons/SkipPreviousRounded';
import Next from '@material-ui/icons/SkipNextRounded';

interface State {
    playPreviousButtonDisabled: boolean;
    playButtonDisabled: boolean;
    playNextButtonDisabled: boolean;
    icon: JSX.Element;
}

const styles = (theme: Theme) => createStyles({
    root: {
        marginTop: '10px',
    },
    sideButton: {
        transform: 'scale(0.7)'
    },
    middleButton: {

    }
});

interface Props extends WithStyles<typeof styles> {}

class PlayPauseControl extends React.Component<Props, State> {

    constructor(props: Props) {
        super(props);
        this.state = PlayPauseControl.getInitialPlayPauseControl();
        this.setCurrentTrack = this.setCurrentTrack.bind(this);
        this.setSideButtonActivity = this.setSideButtonActivity.bind(this);
    }

    componentDidMount() {
        playerState(this.setCurrentTrack);
        playlistChanged(this.setSideButtonActivity)
    }

    setCurrentTrack(currentPlayerState: CurrentPlayerState): void {
        const playerState = currentPlayerState.player_state;
        if (playerState === 'STOPPED') {
            this.setState(PlayPauseControl.getInitialPlayPauseControl());
            return;
        } else if (playerState === 'PAUSED') {
            this.setState( {
                playPreviousButtonDisabled: this.state.playPreviousButtonDisabled,
                playButtonDisabled: false,
                playNextButtonDisabled: this.state.playNextButtonDisabled,
                icon: <PlayArrow/>
            });
            return;
        } else if (playerState === 'PLAYING') {
            this.setState( {
                playPreviousButtonDisabled: this.state.playPreviousButtonDisabled,
                playButtonDisabled: false,
                playNextButtonDisabled: this.state.playNextButtonDisabled,
                icon: <Pause/>,
            });
            return;
        }
        throw new Error('Illegal player state received: ' + playerState);
    }

    setSideButtonActivity(playlistItems: PlaylistItem[]): void {
        const indexOfCurrent = playlistItems.findIndex(playlistItem => playlistItem.status === 'CURRENT');
        const hasCurrentItem = indexOfCurrent >= 0;
        const isCurrentItemNotLast = hasCurrentItem && indexOfCurrent < playlistItems.length - 1;
        this.setState({
            playPreviousButtonDisabled: !hasCurrentItem,
            playButtonDisabled: this.state.playButtonDisabled,
            playNextButtonDisabled: !isCurrentItemNotLast,
            icon: this.state.icon
        });
    }

    static getInitialPlayPauseControl(): State {
        return {
            playPreviousButtonDisabled: true,
            playButtonDisabled: true,
            playNextButtonDisabled: true,
            icon: <PlayArrow/>
        };
    }

    render() {

        const { classes } = this.props;

        return (

            <div className={classes.root}>


                    <Button variant="outlined"
                            color="primary"
                            aria-label="Previous"
                            className={classes.sideButton}
                            disabled={this.state.playPreviousButtonDisabled}
                            onClick={playPreviousTrack}
                            >
                        <Previous/>
                    </Button>

                    <Button variant="outlined"
                            color="primary"
                            aria-label="Play/Pause"
                            className={classes.middleButton}
                            disabled={this.state.playButtonDisabled}
                            onClick={togglePlayPause}
                            >
                        {this.state.icon}
                    </Button>


                    <Button variant="outlined"
                            color="primary"
                            aria-label="Next"
                            className={classes.sideButton}
                            disabled={this.state.playNextButtonDisabled}
                            onClick={playNextTrack}
                            >
                        <Next/>
                    </Button>


            </div>

        );
    }
}
export default withStyles(styles) (PlayPauseControl);
