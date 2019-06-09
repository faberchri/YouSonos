import React from "react";
import classNames from 'classnames';
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
import Grid from '@material-ui/core/Grid';

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
    leftButtonGridItem: {
        textAlign: 'right',
    },
    rightButtonGridItem: {
        textAlign: 'left'
    },
    button: {
        width: 'inherit',
        minWidth: 'inherit',
    },
    leftButton: {
    },
    rightButton: {
    },
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
                icon: <PlayArrow />
            });
            return;
        } else if (playerState === 'PLAYING') {
            this.setState( {
                playPreviousButtonDisabled: this.state.playPreviousButtonDisabled,
                playButtonDisabled: false,
                playNextButtonDisabled: this.state.playNextButtonDisabled,
                icon: <Pause />,
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
            icon: <PlayArrow fontSize="large"/>
        };
    }

    render() {

        const { classes } = this.props;

        return (

            <div className={classes.root}>

                <Grid
                    container
                    direction="row"
                    justify="center"
                    alignItems="center"
                >

                    <Grid item xs={4} className={classes.leftButtonGridItem}>
                        <Button variant="outlined"
                                color="primary"
                                aria-label="Previous"
                                className={classNames(classes.button, classes.leftButton)}
                                disabled={this.state.playPreviousButtonDisabled}
                                onClick={playPreviousTrack}
                                size="small"
                        >

                            <Previous fontSize="small"/>
                        </Button>
                    </Grid>

                    <Grid item xs={4}>
                        <Button variant="outlined"
                                color="primary"
                                aria-label="Play/Pause"
                                className={classes.button}
                                disabled={this.state.playButtonDisabled}
                                onClick={togglePlayPause}
                                size="small"
                        >
                            {this.state.icon}
                        </Button>
                    </Grid>

                    <Grid item xs={4} className={classes.rightButtonGridItem}>
                        <Button variant="outlined"
                                color="primary"
                                aria-label="Next"
                                className={classNames(classes.button, classes.rightButton)}
                                disabled={this.state.playNextButtonDisabled}
                                onClick={playNextTrack}
                                size="small"
                        >
                            <Next fontSize="small"/>
                        </Button>
                    </Grid>
                </Grid>



            </div>

        );
    }
}
export default withStyles(styles) (PlayPauseControl);
