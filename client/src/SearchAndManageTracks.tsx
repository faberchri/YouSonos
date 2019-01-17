import React from "react";
import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core/styles";
import Paper from "@material-ui/core/Paper";
import Search from '@material-ui/icons/SearchRounded';
import List from '@material-ui/icons/List';
import AppBar from '@material-ui/core/AppBar';
import Tabs from '@material-ui/core/Tabs';
import Tab from '@material-ui/core/Tab';
import SearchInput from './SearchInput'
import Playlist from "./Playlist";
import Divider from '@material-ui/core/Divider';
import Badge from '@material-ui/core/Badge';
import {playlistChanged, PlaylistItem} from "./api";


var SwipeableViews = require('react-swipeable-views').default;


interface State {
    index: number,
    playlistSize: number
}

const styles = (theme: Theme) => createStyles({

    paper: {
        paddingLeft: '5px',
        paddingRight: '5px',
        margin: '5px',
        height: '100%',
        display: 'flex',
        flexFlow: 'column',
    },
    tabHeader: {
        backgroundColor: 'inherit',
        boxShadow: 'none'
    },
    slideContainer: {
        display: 'flex',
        flexFlow: 'column',
        height: '100%'
    }
});

interface Props extends WithStyles<typeof styles> {}

class SearchAndManageTracks extends React.Component<Props, State> {


    constructor(props: Props) {
        super(props);
        this.setPlaylistSize = this.setPlaylistSize.bind(this);

        this.state = { index: 0, playlistSize: 0 };
    }

    handleChange = (event: any, index: number) => {
        this.setState({ index: index });
    };

    componentDidMount() {
        playlistChanged(this.setPlaylistSize);
    }

    setPlaylistSize(items: PlaylistItem[]) {
        this.setState({index: this.state.index, playlistSize: items.length})
    }

    render() {

        const { classes } = this.props;

        return (
            <Paper className={classes.paper}>
                <AppBar position="static" color="default" className={classes.tabHeader} >
                    <Tabs
                        value={this.state.index}
                        onChange={this.handleChange}
                        indicatorColor="secondary"
                        textColor="secondary"
                        fullWidth
                    >

                        <Tab icon={<Search/>} />
                        <Tab icon={<Badge badgeContent={this.state.playlistSize}><List/></Badge>} />

                    </Tabs>
                </AppBar>
                <Divider/>
                <SwipeableViews
                    disabled = {true}
                    index={this.state.index}
                    className={classes.slideContainer}
                    slideStyle={{display: 'flex', flexFlow: 'column'}}
                >
                    <SearchInput/>
                    <Playlist />
                </SwipeableViews>
            </Paper>
        );
    }
}
export default withStyles(styles) (SearchAndManageTracks);
