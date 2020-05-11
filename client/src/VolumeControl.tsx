import React from "react";
import {Subject, timer} from "rxjs";
import {debounce} from "rxjs/operators";
import {Device, setVolume, volumeChanged} from "./api";
import Slider from "@material-ui/core/Slider/Slider";
import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core/styles";
import Grid from '@material-ui/core/Grid';
import VolumeDownRounded from '@material-ui/icons/VolumeDownRounded';
import VolumeUpRounded from '@material-ui/icons/VolumeUpRounded';
import IconButton from '@material-ui/core/IconButton';
import classNames from 'classnames';

interface State {
    currentVolume: number;
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
        overflowY: 'hidden',
    },
    slider: {
        paddingTop: '13px',
        paddingBottom: '13px',
        // on phones (device with limited accuracy pointing device) 
        // padding was automatically increased to 20px, we don't want that.
        '@media (pointer: coarse)': {
            padding: '13px 0 !important',
        },
    },
    verticalCentered: {
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
    },
    volumeButtonGridItem: {
        alignItems: 'center',
    },
    volumeButton: {
        width: '30px', // height is also 30px
    }
});

interface Props extends WithStyles<typeof styles> {
    device: Device
}

const VOLUME_BUTTON_CHANGE_STEP_SIZE = 5;

class VolumeControl extends React.Component<Props, State> {

    subject = new Subject<number>();

    constructor(props: Props) {
        super(props);
        this.state = {currentVolume: props.device.current_volume};

        this.updateState = this.updateState.bind(this);
        this.volumeChangeFromServer = this.volumeChangeFromServer.bind(this);

        this.subject
            .pipe(debounce(() => timer(300)))
            .subscribe((volume) => setVolume(this.props.device, volume));
    }

    updateState (event: any, volume: number | number[]): void {
        let newVolume = volume as number;
        this.setState({currentVolume: newVolume});
        this.subject.next(newVolume);
    };

    reduceVolume = (): void => {
        const newVolume = Math.max(this.state.currentVolume - VOLUME_BUTTON_CHANGE_STEP_SIZE, 0);
        this.updateState(undefined, newVolume);
    };

    increaseVolume = (): void => {
        const newVolume = Math.min(this.state.currentVolume + VOLUME_BUTTON_CHANGE_STEP_SIZE, this.props.device.max_volume);
        this.updateState(undefined, newVolume);
    };

    componentDidMount() {
        volumeChanged(this.volumeChangeFromServer);
    }

    volumeChangeFromServer(devices: Device[]): void {
        devices.forEach((device, index) => {
            if (device.device_name === this.props.device.device_name) {
                this.setState({ currentVolume: device.current_volume })
            }
        });
    }

    render() {

        const { classes } = this.props;
        const { currentVolume } = this.state;

        return (
            <Grid container className={classes.root} >
                <Grid item xs={2} className={classNames(classes.verticalCentered, classes.volumeButtonGridItem)}>
                    <IconButton onClick={this.reduceVolume} color="primary" size="small" className={classes.volumeButton}>
                        <VolumeDownRounded />
                    </IconButton>
                </Grid>
                <Grid item xs={8} className={classNames(classes.verticalCentered, classes.sliderContainer)}>
                        {<Slider
                            max={this.props.device.max_volume}
                            value={currentVolume}
                            step={1}
                            onChange={this.updateState}
                            className={classes.slider}
                        />}
                </Grid>
                <Grid item xs={2} className={classNames(classes.verticalCentered, classes.volumeButtonGridItem)}>
                    <IconButton onClick={this.increaseVolume} color="primary" size="small" className={classes.volumeButton}>
                        <VolumeUpRounded />
                    </IconButton>
                </Grid>
            </Grid>
        );
    }
}

export default withStyles(styles) (VolumeControl);
