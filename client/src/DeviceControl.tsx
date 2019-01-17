import React from "react";
import {sonosSetup, Device} from "./api";
import VolumeControl from "./VolumeControl";

import {Theme, withStyles} from "@material-ui/core/styles";
import { WithStyles, createStyles } from '@material-ui/core';
import Grid from "@material-ui/core/Grid/Grid";
import Paper from "@material-ui/core/Paper";


interface State {
    devices: Device[]
}

const styles = (theme: Theme) => createStyles({
    root: {
        margin: '5px',
        paddingTop: '5px',
        paddingBottom: '5px',
        minHeight: '100px',
        overflow: 'auto',
    },

    gridItem: {
    }
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
                        <Grid item xs={12} className={classes.gridItem} key={item.device_name}>
                            <VolumeControl  device={ item }/>
                        </Grid>
                    ))}
                </Grid>
            </Paper>
        );
    }
}
export default withStyles(styles) (DeviceControl);
