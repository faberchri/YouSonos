import React from "react";
import {Device, sonosSetup} from "./api";
import VolumeControl from "./VolumeControl";

import {Theme, withStyles} from "@material-ui/core/styles";
import {createStyles, WithStyles} from '@material-ui/core';
import Grid from "@material-ui/core/Grid/Grid";
import Paper from "@material-ui/core/Paper";
import Typography from "@material-ui/core/Typography";


interface State {
    devices: Device[]
}

const styles = (theme: Theme) => createStyles({
    root: {
        marginLeft: '5px', // no margin on top and bottom in order to have equal margins between components as on sides
        marginRight: '5px',
        paddingTop: '5px',
        paddingBottom: '5px',
        minHeight: '30px', 
        overflowY: 'auto',
        overflowX: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        flex: 0.6,
    },
    gridContainer: {
        display: 'flex',
        flex: 1,
        width: '100%',
    },
    deviceGridItem: {
        display: 'flex',
        flex: '1 1 1',
        width: '100%',
    },
    deviceGridContainer: {
        display: 'flex',
        width: '100%',
    },
    label: {
        marginLeft: '5px',
        overflowX: 'auto',
        textAlign: 'center',
    },
    verticalCentered: {
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
    },
});

interface Props extends WithStyles<typeof styles> {}

class DeviceControl extends React.Component<Props, State> {


    constructor(props: Props) {
        super(props);
        this.state = {devices: []};
        this.setup = this.setup.bind(this)
    }

    componentDidMount() {
        sonosSetup(this.setup);
    }

    setup(devices: Device[]): void {
        this.setState({devices: devices});
    }

    render() {
        const { classes } = this.props;
        return (
            <Paper className={classes.root}>
                <Grid container className={classes.gridContainer}>
                    {this.state.devices.map((item, index) => (
                        <Grid item xs={12} key={item.device_name + index} className={classes.deviceGridItem}>
                            <Grid container className={classes.deviceGridContainer}>
                                <Grid item xs={3} className={classes.verticalCentered}>
                                    <Typography variant={"body2"} className={classes.label}>{item.device_name}</Typography>
                                </Grid>
                                <Grid item xs={9} className={classes.verticalCentered}>
                                    <VolumeControl  device={ item }/>
                                </Grid>
                            </Grid>
                        </Grid>
                    ))}
                </Grid>
            </Paper>
        );
    }
}
export default withStyles(styles) (DeviceControl);
