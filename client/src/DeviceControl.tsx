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
        margin: '5px',
        paddingTop: '5px',
        paddingBottom: '5px',
        minHeight: '100px',
        overflowY: 'auto',
        overflowX: 'hidden',
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
                <Grid container>
                    {this.state.devices.map((item, index) => (
                        <Grid item xs={12} key={item.device_name}>
                            <Grid container>
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
