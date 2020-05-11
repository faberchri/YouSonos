import React from "react";
import classNames from 'classnames';


import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core/styles";
import Grid from "@material-ui/core/Grid/Grid";
import Typography from "@material-ui/core/Typography";
import IconButton from "@material-ui/core/IconButton";
import Slider from "@material-ui/core/Slider";
import Replay10Icon from "@material-ui/icons/Replay10Rounded";
import Forward10Icon from "@material-ui/icons/Forward10Rounded";
import {formatDuration, playerTime, playerTimeUpdateActivation, seekTo, Track} from "./api";
import {Subject, timer} from "rxjs";
import {debounce} from "rxjs/operators";


interface State {
    playerTime: number;
    playerTimeUpdateActive: boolean;
}

const styles = (theme: Theme) => createStyles({
    root: {
    },
    // fix scrollbar issue.
    // See: https://github.com/mui-org/material-ui/issues/13649 and https://github.com/mui-org/material-ui/issues/13455
    sliderContainer: {
        paddingLeft: '7px',
        paddingRight: '7px',
        overflowX: 'hidden',
        overflowY: 'hidden' // only for Safari
    },
    label: {
    },
    paper: {
    },
    verticalCentered: {
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
    },
    time: {
        marginTop: '-19px'
    },
    currentTime: {
        textAlign: 'left',
        paddingLeft: '10%'
    },
    totalTime: {
        textAlign: 'right',
        paddingRight: '10%'
    },
    positionChangeButton: {
        marginLeft: '-15px'
    },

});


interface Props extends WithStyles<typeof styles> {
    track: Track
}

class TrackProgressControl extends React.Component<Props, State> {

    subject = new Subject<number>();

    constructor(props: Props) {
        super(props);
        this.state = {
            playerTime: 0,
            playerTimeUpdateActive: true,
        };

        this.subject
            .pipe(debounce(() => timer(750)))
            .subscribe((new_time) => seekTo(new_time));
    }

    componentDidMount() {
        playerTime(this.setPlayerTimeIfActive);
        playerTimeUpdateActivation(this.activatePlayerTimeUpdate);
    }

    private setPlayerTimeIfActive = (time: number): void => {
        if (this.state.playerTimeUpdateActive) {
            this.setPlayerTime(time)
        }
    };

    private setPlayerTime = (time: number): void => {
        this.setState({
            playerTime: time,
            playerTimeUpdateActive: this.state.playerTimeUpdateActive
        });
    };

    tenSecondsReplay = (): void => {
        this.enqueueSeekEvent(this.state.playerTime - 10 * 1000);
    };

    tenSecondsForward = (): void => {
        this.enqueueSeekEvent(this.state.playerTime + 10 * 1000);
    };

    changePosition = (event: any, value: number | number[]): void => {
        let newTime = value as number;
        this.enqueueSeekEvent(newTime);
    };

    getPlayerTimeString = (): string => {
        return formatDuration(this.state.playerTime);
    };

    getDurationString = (): string => {
        return formatDuration(this.props.track.duration);
    };

    private enqueueSeekEvent = (newTime: number): void => {
        this.setState({
            playerTime: newTime,
            playerTimeUpdateActive: false
        });
        this.subject.next(newTime);
    };

    private activatePlayerTimeUpdate = (time: number): void => {
        this.setState({
            playerTime: time,
            playerTimeUpdateActive: true
        });
    };


    render() {

        const { classes } = this.props;
        const { playerTime } = this.state;

        const disabled = this.props.track.track_type === 'null';

        return (

            <Grid container className={classes.root}>

                <Grid item xs={1}>
                    <IconButton onClick={this.tenSecondsReplay} color="primary" className={classes.positionChangeButton} disabled={disabled}>
                        <Replay10Icon fontSize="small"/>
                    </IconButton>
                </Grid>
                <Grid item xs={10} className={classNames(classes.verticalCentered, classes.sliderContainer)}>
                    {<Slider
                        max={this.props.track.duration}
                        value={playerTime}
                        onChange={this.changePosition}
                        disabled={disabled}
                        step={1}
                    />}
                </Grid>

                <Grid item xs={1}>
                    <IconButton onClick={this.tenSecondsForward} color="primary" className={classes.positionChangeButton} disabled={disabled}>
                        <Forward10Icon fontSize="small"/>
                    </IconButton>
                </Grid>
                <Grid item xs={6} className={classNames(classes.time, classes.currentTime)} >
                    <Typography className={classes.label} variant="caption" align={"left"}>{this.getPlayerTimeString()}</Typography>
                </Grid>
                <Grid item xs={6} className={classNames(classes.time, classes.totalTime)}>
                    <Typography className={classes.label} variant="caption" align={"right"}>{this.getDurationString()}</Typography>
                </Grid>
            </Grid>


        );
    }
}
export default withStyles(styles) (TrackProgressControl);
